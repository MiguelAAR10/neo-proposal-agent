"""
load_data.py — CSV → Gemini Embeddings → Qdrant
Run once: python load_data.py
"""
import os
import sys
import time
import hashlib
import pandas as pd
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# --- Config ---
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY") # Usamos la misma clave
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = "neo_casos" # Nombre estándar de la Business Case
CSV_PATH = "Databases-Cases.csv"

# Modelos Gemini Embedding
EMBEDDING_MODEL_PRIMARY = "gemini-embedding-001"
BATCH_SIZE = 10
MAX_RETRIES = 3

# Mapeo de columnas CSV → nombres estándar API
COLUMN_MAPPING = {
    "id_caso": "id",
    "nombre_empresa_crudo": "empresa_nombre",
    "industria_detectada": "industria",
    "area_detectada": "area_funcional",
    "tipo_problema_detectado": "problema_descripcion",
    "solucion_detectada": "solucion_descripcion",
    "resultados_detectados": "resultados_kpis",
    "tecnologias_mencionadas": "tecnologias",
    "url_slide": "fuente_url",
    "trigger_comercial_detectado": "trigger_comercial",
    "contexto_para_embedding": "texto_embedding",
}

def validate_env():
    missing = []
    if not GOOGLE_API_KEY: missing.append("GEMINI_API_KEY")
    if not QDRANT_URL: missing.append("QDRANT_URL")
    if not QDRANT_API_KEY: missing.append("QDRANT_API_KEY")
    if missing:
        print(f"❌ Missing: {', '.join(missing)}")
        sys.exit(1)

def id_to_int(id_val) -> int:
    id_str = str(id_val)
    return int(hashlib.md5(id_str.encode()).hexdigest()[:8], 16)

def build_embedding_text(row: pd.Series) -> str:
    contexto = row.get("contexto_para_embedding")
    if pd.notna(contexto) and str(contexto).strip() and str(contexto).lower() != "nan":
        return str(contexto)
    return f"Empresa: {row.get('nombre_empresa_crudo')} | Problema: {row.get('tipo_problema_detectado')}"

def normalize_payload(row: pd.Series) -> dict:
    payload = {}
    for csv_col, api_col in COLUMN_MAPPING.items():
        if csv_col in row.index:
            valor = row[csv_col]
            if pd.notna(valor):
                if api_col == "tecnologias" and isinstance(valor, str):
                    payload[api_col] = [t.strip() for t in valor.split() if t.strip()]
                else:
                    payload[api_col] = str(valor).strip()
    return payload

def embed_batch(client: genai.Client, texts: list[str], model: str) -> list[list[float]]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = client.models.embed_content(model=model, contents=texts)
            return [e.values for e in result.embeddings]
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
            else:
                raise

def main():
    validate_env()
    df = pd.read_csv(CSV_PATH)
    print(f"✅ CSV cargado: {len(df)} casos")
    
    texts = [build_embedding_text(row) for _, row in df.iterrows()]
    genai_client = genai.Client(api_key=GOOGLE_API_KEY)
    all_embeddings = []
    
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Generando Embeddings"):
        batch = texts[i:i + BATCH_SIZE]
        all_embeddings.extend(embed_batch(genai_client, batch, EMBEDDING_MODEL_PRIMARY))
    
    vector_dim = len(all_embeddings[0])
    # Mayor timeout para evitar errores de red
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)
    
    try:
        qdrant.delete_collection(COLLECTION)
    except Exception: pass
    
    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
    )
    
    points = [
        PointStruct(id=id_to_int(row["id_caso"]), vector=all_embeddings[idx], payload=normalize_payload(row))
        for idx, (_, row) in enumerate(df.iterrows())
    ]
    
    # Subir en chunks de 20
    chunk_size = 20
    for i in range(0, len(points), chunk_size):
        qdrant.upsert(collection_name=COLLECTION, points=points[i:i+chunk_size])
    
    print(f"🚀 {len(points)} casos cargados exitosamente en la colección '{COLLECTION}'")

if __name__ == "__main__":
    main()
