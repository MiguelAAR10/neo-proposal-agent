"""
load_data.py — CSV → Gemini Embeddings → Qdrant
Run once: python load_data.py
Based on the working ChatBot-BusinessCase architecture.
"""
import hashlib
import os
import sys
import time

import pandas as pd
from dotenv import load_dotenv
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

load_dotenv()

# --- Config ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = os.getenv("QDRANT_COLLECTION", "neo_casos")
CSV_PATH = os.getenv("CSV_PATH", "Databases-Cases.csv")

# ✅ Único modelo de embedding disponible confirmado via API
EMBEDDING_MODEL = "gemini-embedding-001"
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
    missing = [v for v in ["GOOGLE_API_KEY", "QDRANT_URL", "QDRANT_API_KEY"] if not os.getenv(v)]
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        sys.exit(1)


def id_to_int(id_val) -> int:
    return int(hashlib.md5(str(id_val).encode()).hexdigest()[:8], 16)


def build_embedding_text(row: pd.Series) -> str:
    """Usa contexto_para_embedding si existe, sino construye el texto."""
    contexto = row.get("contexto_para_embedding")
    if pd.notna(contexto) and str(contexto).strip() and str(contexto).lower() != "nan":
        return str(contexto)

    partes = []
    campos = [
        ("nombre_empresa_crudo", "Empresa"),
        ("industria_detectada", "Industria"),
        ("tipo_problema_detectado", "Problema"),
        ("solucion_detectada", "Solución"),
        ("resultados_detectados", "Resultados"),
    ]
    for campo, label in campos:
        valor = row.get(campo)
        if pd.notna(valor) and str(valor).strip() and str(valor).lower() != "nan":
            partes.append(f"{label}: {valor}")
    return " | ".join(partes) if partes else f"Caso {row.get('id_caso', 'sin ID')}"


def normalize_payload(row: pd.Series) -> dict:
    payload = {}
    for csv_col, api_col in COLUMN_MAPPING.items():
        if csv_col in row.index:
            valor = row[csv_col]
            if pd.notna(valor):
                if api_col == "tecnologias" and isinstance(valor, str):
                    payload[api_col] = [t.strip() for t in valor.split(",") if t.strip()]
                else:
                    payload[api_col] = str(valor).strip()

    defaults = {
        "titulo_corto": lambda: f"Caso {payload.get('empresa_nombre', 'NEO')}",
        "empresa_nombre": "Empresa no especificada",
        "industria": "No especificada",
        "area_funcional": "No especificada",
        "problema_descripcion": "Problema no documentado",
        "solucion_descripcion": "Solución no documentada",
        "resultados_kpis": "",
        "tecnologias": [],
        "fuente_url": "",
        "trigger_comercial": "",
    }
    for campo, default in defaults.items():
        if campo not in payload or not payload[campo]:
            payload[campo] = default() if callable(default) else default
    return payload


def embed_batch(client: genai.Client, texts: list[str]) -> list[list[float]]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
            )
            return [e.values for e in result.embeddings]
        except Exception as e:
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt
                print(f"   ⚠️ Intento {attempt} falló: {e}. Reintentando en {wait}s...")
                time.sleep(wait)
            else:
                raise


def main():
    print("=" * 60)
    print("🚀 NEO Case Loader")
    print(f"   Modelo: {EMBEDDING_MODEL}")
    print(f"   Colección: {COLLECTION}")
    print("=" * 60)

    validate_env()

    # 1. Leer CSV
    if not os.path.exists(CSV_PATH):
        print(f"❌ No encontrado: {CSV_PATH}")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    print(f"\n✅ CSV cargado: {len(df)} casos")
    print(f"   Columnas: {', '.join(df.columns.tolist())}")

    # 2. Preparar textos
    print(f"\n📝 Preparando textos para embedding...")
    texts = [build_embedding_text(row) for _, row in df.iterrows()]
    print(f"   Ejemplo (caso 1): {texts[0][:120]}...")

    # 3. Generar embeddings
    print(f"\n🤖 Generando embeddings con {EMBEDDING_MODEL}...")
    g_client = genai.Client(api_key=GOOGLE_API_KEY)
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        print(f"   Batch {i//BATCH_SIZE + 1}/{(len(texts)-1)//BATCH_SIZE + 1} ({len(batch)} textos)...")
        embeddings = embed_batch(g_client, batch)
        all_embeddings.extend(embeddings)

    vector_dim = len(all_embeddings[0])
    print(f"\n✅ {len(all_embeddings)} embeddings generados (dim={vector_dim})")

    # 4. Conectar Qdrant
    print(f"\n🗄️  Conectando a Qdrant...")
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # 5. Recrear colección
    try:
        qdrant.delete_collection(COLLECTION)
        print(f"   🗑️  Colección '{COLLECTION}' eliminada")
    except Exception:
        pass

    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
    )
    print(f"   ✅ Colección '{COLLECTION}' creada (dim={vector_dim})")

    # 6. Insertar casos
    print(f"\n💾 Insertando {len(df)} casos...")
    points = []
    for idx, (_, row) in enumerate(df.iterrows()):
        payload = normalize_payload(row)
        points.append(
            PointStruct(
                id=id_to_int(row["id_caso"]),
                vector=all_embeddings[idx],
                payload=payload,
            )
        )

    qdrant.upsert(collection_name=COLLECTION, points=points)

    # 7. Resumen
    print(f"\n{'=' * 60}")
    print("🎉 ¡Carga completada!")
    print(f"{'=' * 60}")
    print(f"\n📊 Resumen:")
    print(f"   • Casos cargados : {len(points)}")
    print(f"   • Dimensión      : {vector_dim}")
    print(f"   • Colección      : {COLLECTION}")
    print(f"\n🚀 Siguiente paso:")
    print(f"   uvicorn api:app --reload --port 8000")
    print(f"   streamlit run app.py")


if __name__ == "__main__":
    main()
