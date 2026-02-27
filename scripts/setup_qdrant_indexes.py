import sys
from pathlib import Path

# Añadir el backend al path
sys.path.append(str(Path(__file__).parent / "backend"))

from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import get_settings

def setup_indexes():
    print("⚙️ Configurando índices de payload en Qdrant...")
    
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    
    # 1. Índices para neo_cases_v1
    print(f"Configurando índices para {settings.qdrant_collection_cases}...")
    client.create_payload_index(
        collection_name=settings.qdrant_collection_cases,
        field_name="tipo",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=settings.qdrant_collection_cases,
        field_name="rubro",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    
    # 2. Índices para neo_profiles_v1
    print(f"Configurando índices para {settings.qdrant_collection_profiles}...")
    client.create_payload_index(
        collection_name=settings.qdrant_collection_profiles,
        field_name="empresa",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=settings.qdrant_collection_profiles,
        field_name="area",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    
    print("✅ Índices configurados con éxito.")

if __name__ == "__main__":
    try:
        setup_indexes()
    except Exception as e:
        print(f"❌ Error configurando índices: {e}")
