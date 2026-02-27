import sys
from pathlib import Path

# Añadir el backend al path
sys.path.append(str(Path(__file__).parent / "backend"))

from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import get_settings

def update_case_types():
    print("🏷️ Actualizando tipos de casos (AI/NEO) para MVP V2...")
    
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    collection_name = settings.qdrant_collection_cases
    
    # Obtener todos los casos
    scroll_result = client.scroll(
        collection_name=collection_name,
        limit=1000,
        with_payload=True,
        with_vectors=False
    )
    
    points = scroll_result[0]
    
    for point in points:
        payload = point.payload
        source = payload.get("source", "").lower()
        
        # Determinar el tipo basado en el nombre del archivo fuente
        if "ai_cases" in source:
            tipo = "AI"
        elif "neo_legacy" in source:
            tipo = "NEO"
        else:
            tipo = "NEO" # Default
            
        # Actualizar solo el campo 'tipo'
        client.set_payload(
            collection_name=collection_name,
            payload={"tipo": tipo},
            points=[point.id]
        )
    
    print(f"✅ Se han procesado {len(points)} casos con éxito.")

if __name__ == "__main__":
    try:
        update_case_types()
    except Exception as e:
        print(f"❌ Error actualizando casos: {e}")
