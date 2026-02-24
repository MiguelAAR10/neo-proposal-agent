import csv
import hashlib
from pathlib import Path
from typing import Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models

from src.config import get_settings


class QdrantConnection:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: QdrantClient | None = None
        self._embeddings: GoogleGenerativeAIEmbeddings | None = None
        self._embedding_model: str | None = None

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

    def _candidate_embedding_models(self) -> list[str]:
        env_model = self._settings.gemini_embedding_model.strip()
        candidates = []
        if env_model:
            candidates.append(env_model)

        # Fallbacks comunes entre endpoints/versiones.
        candidates.extend(
            [
                "models/text-embedding-004",
                "text-embedding-004",
            ]
        )

        seen: set[str] = set()
        deduped: list[str] = []
        for m in candidates:
            if m not in seen:
                seen.add(m)
                deduped.append(m)
        return deduped

    def _build_embeddings(self, model_name: str) -> GoogleGenerativeAIEmbeddings:
        if not self._settings.gemini_api_key:
            raise ValueError("Falta configurar GEMINI_API_KEY")
        return GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=self._settings.gemini_api_key,
        )

    def _ensure_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        if self._embeddings is not None:
            return self._embeddings

        # Tomamos el modelo desde configuración tipada.
        model_name = self._settings.gemini_embedding_model.strip()
        
        try:
            self._embeddings = self._build_embeddings(model_name)
            self._embedding_model = model_name
            print(f"✅ Embeddings inicializados usando el modelo: {model_name}")
            return self._embeddings
        except Exception as exc:
            raise RuntimeError(f"Fallo crítico al inicializar Gemini Embeddings ({model_name}). Revisa tu API KEY. Error: {exc}")
        
    def _point_id_from_external(self, external_id: str) -> int:
        digest = hashlib.sha1(external_id.encode("utf-8")).hexdigest()
        return int(digest[:16], 16)

    def _compose_text_for_embedding(self, row: dict[str, Any]) -> str:
        preferred_fields = [
            "contexto_para_embedding",
            "texto_completo_slide",
            "descripcion_reto",
            "descripcion_solucion",
            "resultados_mencionados",
            "problema",
            "solucion_detectada",
            "resultados_detectados",
        ]
        parts = [str(row.get(k, "")).strip() for k in preferred_fields if str(row.get(k, "")).strip()]
        if parts:
            return " | ".join(parts)
        return " | ".join(str(v).strip() for v in row.values() if str(v).strip())

    def _normalize_case_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        case_id = str(
            row.get("id_caso")
            or row.get("id")
            or row.get("case_id")
            or f"CASE-{hashlib.md5(str(row).encode('utf-8')).hexdigest()[:8]}"
        ).strip()
        empresa = str(row.get("nombre_empresa_crudo") or row.get("cliente_mencionado") or "").strip()
        rubro = str(row.get("industria_detectada") or row.get("industria_pdf") or "").strip()
        titulo = str(row.get("titulo_caso") or row.get("trigger_comercial_detectado") or "").strip()
        resumen = str(
            row.get("contexto_para_embedding")
            or row.get("texto_completo_slide")
            or row.get("descripcion_reto")
            or row.get("problema")
            or ""
        ).strip()

        return {
            "id": case_id,
            "empresa": empresa,
            "rubro": rubro,
            "titulo": titulo or f"Caso {case_id}",
            "resumen": resumen or "Sin resumen",
            "source": str(row.get("_source_file", "")).strip(),
            "raw": row,
        }

    def ensure_collection(self, collection_name: str = "neo_cases_v1") -> None:
        client = self._ensure_client()
        embeddings = self._ensure_embeddings()
        probe = embeddings.embed_query("dimension probe")
        vector_size = len(probe)

        existing = {c.name for c in client.get_collections().collections}
        if collection_name in existing:
            return

        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )

    def upsert_cases(self, rows: list[dict[str, Any]], collection_name: str = "neo_cases_v1") -> int:
        if not rows:
            return 0

        self.ensure_collection(collection_name=collection_name)
        embeddings = self._ensure_embeddings()
        client = self._ensure_client()

        normalized = [self._normalize_case_payload(r) for r in rows]
        texts = [self._compose_text_for_embedding(n["raw"]) for n in normalized]
        vectors = embeddings.embed_documents(texts)

        points: list[models.PointStruct] = []
        for payload, vector in zip(normalized, vectors):
            points.append(
                models.PointStruct(
                    id=self._point_id_from_external(payload["id"]),
                    vector=vector,
                    payload=payload,
                )
            )

        client.upsert(collection_name=collection_name, points=points)
        return len(points)

    def load_csv_files(self, csv_paths: list[str], collection_name: str = "neo_cases_v1") -> int:
        all_rows: list[dict[str, Any]] = []
        for file_path in csv_paths:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                continue
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row["_source_file"] = str(path)
                    all_rows.append(row)

        return self.upsert_cases(all_rows, collection_name=collection_name)

    def search_cases(self, problem_text: str, collection_name: str = "neo_cases_v1", limit: int = 6) -> list[dict[str, Any]]:
        client = self._ensure_client()
        embeddings = self._ensure_embeddings()
        query_vector = embeddings.embed_query(problem_text)

        points = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )

        results: list[dict[str, Any]] = []
        for point in points:
            payload = point.payload or {}
            case_id = str(payload.get("id") or point.id)
            results.append(
                {
                    "id": case_id,
                    "score": float(point.score),
                    "titulo": str(payload.get("titulo") or f"Caso {case_id}"),
                    "resumen": str(payload.get("resumen") or "Sin resumen"),
                    "empresa": str(payload.get("empresa") or ""),
                    "rubro": str(payload.get("rubro") or ""),
                    "payload": payload,
                }
            )
        return results


db_connection = QdrantConnection()
