from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Any, Literal

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import ValidationError
from qdrant_client import QdrantClient
from qdrant_client.http import models
import requests

from src.config import get_settings
from src.models.case import CaseInput, CaseQdrant

logger = logging.getLogger(__name__)


class QdrantConnection:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: QdrantClient | None = None
        self._embeddings: GoogleGenerativeAIEmbeddings | None = None
        self._embedding_model: str = self._settings.gemini_embedding_model

    def _ensure_client(self) -> QdrantClient:
        if self._client is not None:
            return self._client
        if not self._settings.qdrant_url:
            raise ValueError("Falta configurar QDRANT_URL")
        self._client = QdrantClient(
            url=self._settings.qdrant_url,
            api_key=self._settings.qdrant_api_key,
        )
        return self._client

    def _ensure_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        if self._embeddings is not None:
            return self._embeddings

        if not self._settings.gemini_api_key:
            raise ValueError("Falta configurar GEMINI_API_KEY")

        try:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model=self._embedding_model,
                google_api_key=self._settings.gemini_api_key,
            )
            return self._embeddings
        except Exception as exc:
            raise RuntimeError(f"Fallo crítico al inicializar Gemini Embeddings: {exc}")

    def _ensure_cases_collection(self, collection_name: str) -> None:
        client = self._ensure_client()
        existing = {c.name for c in client.get_collections().collections}
        if collection_name in existing:
            return

        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
        )

    def reset_cases_collection(self, collection_name: str) -> None:
        client = self._ensure_client()
        existing = {c.name for c in client.get_collections().collections}
        if collection_name in existing:
            client.delete_collection(collection_name=collection_name)
        self._ensure_cases_collection(collection_name)

    @staticmethod
    def _normalize_url(raw: str | None) -> str | None:
        value = (raw or "").strip()
        if not value:
            return None
        if value.lower() in {"pendiente", "n/a", "na", "none", "null", "-"}:
            return None
        if re.match(r"^https?://", value, flags=re.IGNORECASE):
            return value
        return None

    @staticmethod
    def _parse_list(raw: str | None) -> list[str]:
        if raw is None:
            return []
        text = str(raw).strip()
        if not text:
            return []

        parts = re.split(r"\s*//\s*|\s*,\s*|\s*;\s*", text)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _clean_text(value: str | None) -> str:
        return (value or "").strip()

    def _normalize_ai_row(self, row: dict[str, str], source_name: str) -> CaseInput:
        case = CaseInput(
            case_id=self._clean_text(row.get("id_caso")),
            tipo="AI",
            titulo=self._clean_text(row.get("trigger_comercial_detectado"))
            or self._clean_text(row.get("solucion_detectada"))[:120],
            empresa=self._clean_text(row.get("nombre_empresa_crudo")) or None,
            industria=self._clean_text(row.get("industria_detectada")) or None,
            area=self._clean_text(row.get("area_detectada")) or None,
            problema=self._clean_text(row.get("tipo_problema_detectado")),
            solucion=self._clean_text(row.get("solucion_detectada")),
            beneficios=self._parse_list(row.get("resultados_detectados")),
            stack=self._parse_list(row.get("tecnologias_mencionadas")),
            kpi_impacto=self._clean_text(row.get("resultados_detectados")) or None,
            url_slide=self._normalize_url(row.get("url_slide")),
            origen=source_name,
        )
        return case

    def _normalize_neo_row(self, row: dict[str, str], source_name: str) -> CaseInput:
        url = self._normalize_url(row.get("url_slide")) or self._normalize_url(row.get("google_slides_url"))
        case = CaseInput(
            case_id=self._clean_text(row.get("id_caso")),
            tipo="NEO",
            titulo=self._clean_text(row.get("titulo_caso")),
            empresa=self._clean_text(row.get("cliente_mencionado")) or None,
            industria=self._clean_text(row.get("industria_pdf")) or None,
            area=self._clean_text(row.get("area_funcional_mencionada")) or None,
            problema=self._clean_text(row.get("descripcion_reto")),
            solucion=self._clean_text(row.get("descripcion_solucion")),
            beneficios=self._parse_list(row.get("resultados_mencionados")),
            stack=self._parse_list(row.get("tecnologias_mencionadas")),
            kpi_impacto=self._clean_text(row.get("resultados_mencionados")) or None,
            url_slide=url,
            origen=source_name,
        )
        return case

    def _build_embedding_text(self, payload: dict[str, Any]) -> str:
        beneficios = ", ".join(payload.get("beneficios", []))
        stack = ", ".join(payload.get("stack", []))
        return (
            f"Titulo: {payload.get('titulo', '')}\n"
            f"Industria: {payload.get('industria') or 'No mapeado'}\n"
            f"Area: {payload.get('area') or 'No mapeado'}\n"
            f"Problema: {payload.get('problema', '')}\n"
            f"Solucion: {payload.get('solucion', '')}\n"
            f"Beneficios: {beneficios or 'No mapeado'}\n"
            f"Tecnologias: {stack or 'No mapeado'}"
        )

    def load_csv_files(self, csv_files: list[str], collection_name: str = "neo_cases_v1") -> dict[str, Any]:
        self._ensure_cases_collection(collection_name)
        client = self._ensure_client()
        embeddings = self._ensure_embeddings()

        points: list[models.PointStruct] = []
        seen_ids: set[str] = set()
        valid_count = 0
        rejected_count = 0
        missing_url_count = 0
        with_url_count = 0
        source_stats: dict[str, dict[str, int]] = {}

        for csv_path in csv_files:
            source = Path(csv_path).name
            source_stats.setdefault(source, {"valid": 0, "rejected": 0, "with_url": 0, "missing_url": 0})
            with Path(csv_path).open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        if "ai_cases" in source:
                            case_input = self._normalize_ai_row(row, source)
                        elif "neo_legacy" in source:
                            case_input = self._normalize_neo_row(row, source)
                        else:
                            rejected_count += 1
                            logger.warning("CSV no soportado para normalizacion: %s", source)
                            continue

                        if case_input.case_id in seen_ids:
                            raise ValueError(f"case_id duplicado detectado: {case_input.case_id}")
                        seen_ids.add(case_input.case_id)

                        case_payload = CaseQdrant.from_input(case_input).model_dump()
                        if case_payload.get("url_slide"):
                            with_url_count += 1
                            source_stats[source]["with_url"] += 1
                        else:
                            missing_url_count += 1
                            source_stats[source]["missing_url"] += 1
                        embedding_text = self._build_embedding_text(case_payload)
                        vector = embeddings.embed_query(embedding_text)

                        points.append(
                            models.PointStruct(
                                id=case_payload["case_id"],
                                vector=vector,
                                payload=case_payload,
                            )
                        )
                        valid_count += 1
                        source_stats[source]["valid"] += 1
                    except (ValidationError, ValueError) as exc:
                        rejected_count += 1
                        source_stats[source]["rejected"] += 1
                        logger.warning("Fila rechazada en %s: %s", source, exc)
                    except Exception as exc:
                        rejected_count += 1
                        source_stats[source]["rejected"] += 1
                        logger.exception("Error inesperado en ingesta %s: %s", source, exc)

                    if len(points) >= 32:
                        client.upsert(collection_name=collection_name, points=points)
                        points.clear()

        if points:
            client.upsert(collection_name=collection_name, points=points)

        summary = {
            "collection": collection_name,
            "valid": valid_count,
            "rejected": rejected_count,
            "with_url": with_url_count,
            "missing_url": missing_url_count,
            "source_stats": source_stats,
        }

        logger.info("Ingesta completada: %s", summary)
        return summary

    def embed_query(self, query: str) -> list[float]:
        embeddings = self._ensure_embeddings()
        return embeddings.embed_query(query)

    def search_cases_by_vector(
        self,
        query_vector: list[float],
        switch: Literal["neo", "ai", "both"] = "both",
        limit: int = 6,
        score_threshold: float = 0.50,
        timeout_sec: float = 1.0,
    ) -> list[dict[str, Any]]:
        client = self._ensure_client()

        search_filter = None
        if switch == "neo":
            search_filter = models.Filter(
                must=[models.FieldCondition(key="tipo", match=models.MatchValue(value="NEO"))]
            )
        elif switch == "ai":
            search_filter = models.Filter(
                must=[models.FieldCondition(key="tipo", match=models.MatchValue(value="AI"))]
            )

        results = client.search(
            collection_name=self._settings.qdrant_collection_cases,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=limit,
            score_threshold=score_threshold,
            timeout=max(1, int(timeout_sec)),
            with_payload=True,
        )

        return [
            {
                "id": str(hit.id),
                "score": float(hit.score),
                **(hit.payload or {}),
            }
            for hit in results
        ]

    def search_cases(
        self,
        query: str,
        switch: Literal["neo", "ai", "both"] = "both",
        limit: int = 6,
        score_threshold: float = 0.50,
        timeout_sec: float = 1.0,
    ) -> list[dict[str, Any]]:
        query_vector = self.embed_query(query)
        return self.search_cases_by_vector(
            query_vector=query_vector,
            switch=switch,
            limit=limit,
            score_threshold=score_threshold,
            timeout_sec=timeout_sec,
        )

    def get_profile(self, empresa: str, area: str) -> dict[str, Any] | None:
        client = self._ensure_client()

        exact_results = client.scroll(
            collection_name=self._settings.qdrant_collection_profiles,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(key="empresa", match=models.MatchValue(value=empresa)),
                    models.FieldCondition(key="area", match=models.MatchValue(value=area)),
                ]
            ),
            limit=1,
            with_payload=True,
        )

        points = exact_results[0]
        if points:
            return points[0].payload

        company_only = client.scroll(
            collection_name=self._settings.qdrant_collection_profiles,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="empresa", match=models.MatchValue(value=empresa))]
            ),
            limit=1,
            with_payload=True,
        )
        points = company_only[0]
        if points:
            payload = dict(points[0].payload or {})
            payload.setdefault("notas", "Perfil parcial por empresa (area no mapeada)")
            return payload
        return None

    def upsert_profile(self, profile_data: dict[str, Any]) -> None:
        client = self._ensure_client()

        empresa = profile_data.get("empresa", "unknown")
        area = profile_data.get("area", "general")
        point_id = f"{empresa}-{area}".strip().lower().replace(" ", "_")

        client.upsert(
            collection_name=self._settings.qdrant_collection_profiles,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=[0.0] * 768,
                    payload=profile_data,
                )
            ],
        )

    @staticmethod
    def _classify_link_status(url: str | None) -> str:
        if not url:
            return "unknown"

        try:
            resp = requests.head(url, allow_redirects=True, timeout=5)
            if resp.status_code == 405:
                resp = requests.get(url, allow_redirects=True, timeout=5)
            if 200 <= resp.status_code < 400:
                return "verified"
            if resp.status_code in {401, 403, 404, 410}:
                return "inaccessible"
            return "unknown"
        except requests.RequestException:
            return "unknown"

    def verify_links_status(
        self,
        collection_name: str | None = None,
        batch_size: int = 64,
    ) -> dict[str, int]:
        client = self._ensure_client()
        target_collection = collection_name or self._settings.qdrant_collection_cases

        offset = None
        updated = 0
        verified = 0
        inaccessible = 0
        unknown = 0

        while True:
            points, next_offset = client.scroll(
                collection_name=target_collection,
                offset=offset,
                limit=batch_size,
                with_payload=True,
            )
            if not points:
                break

            for point in points:
                payload = point.payload or {}
                status = self._classify_link_status(payload.get("url_slide"))
                client.set_payload(
                    collection_name=target_collection,
                    payload={"link_status": status},
                    points=[point.id],
                )
                updated += 1
                if status == "verified":
                    verified += 1
                elif status == "inaccessible":
                    inaccessible += 1
                else:
                    unknown += 1

            if next_offset is None:
                break
            offset = next_offset

        return {
            "updated": updated,
            "verified": verified,
            "inaccessible": inaccessible,
            "unknown": unknown,
        }


# Instancia global para ser usada en nodos y API
db_connection = QdrantConnection()
