import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models

from src.config import get_settings


class QdrantConnection:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: QdrantClient | None = None
        self._embeddings: GoogleGenerativeAIEmbeddings | None = None
        # Usamos el modelo configurado o el default de V1
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

    def search_cases(
        self, 
        query: str, 
        switch: Literal["neo", "ai", "both"] = "both", 
        limit: int = 6
    ) -> list[dict]:
        """Busca casos en Qdrant con filtro por tipo (Switch)."""
        client = self._ensure_client()
        embeddings = self._ensure_embeddings()
        
        query_vector = embeddings.embed_query(query)
        
        # Construir filtro según switch
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
            with_payload=True
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                **(hit.payload or {})
            }
            for hit in results
        ]

    def get_profile(self, empresa: str, area: str) -> dict | None:
        """Recupera el perfil del cliente (Dummy o Real) desde Qdrant."""
        client = self._ensure_client()
        
        # Búsqueda exacta por empresa y área en el payload
        results = client.scroll(
            collection_name=self._settings.qdrant_collection_profiles,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(key="empresa", match=models.MatchValue(value=empresa)),
                    models.FieldCondition(key="area", match=models.MatchValue(value=area)),
                ]
            ),
            limit=1,
            with_payload=True
        )
        
        points = results[0]
        if points:
            return points[0].payload
        return None

    def upsert_profile(self, profile_data: dict) -> None:
        """Guarda o actualiza un perfil de cliente."""
        client = self._ensure_client()
        
        # Generar un ID determinista basado en empresa y área
        empresa = profile_data.get("empresa", "unknown")
        area = profile_data.get("area", "general")
        point_id = hashlib.md5(f"{empresa}-{area}".lower().encode()).hexdigest()
        
        client.upsert(
            collection_name=self._settings.qdrant_collection_profiles,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=[0.0] * 768, # Placeholder si no vectorizamos el perfil aún
                    payload=profile_data
                )
            ]
        )

# Instancia global para ser usada en los nodos
db_connection = QdrantConnection()
