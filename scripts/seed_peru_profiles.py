import hashlib
import sys
from pathlib import Path

# Añadir el backend al path para poder importar src
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from src.tools.qdrant_tool import db_connection
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import get_settings

def seed_profiles():
    print("🇵🇪 Iniciando siembra de perfiles corporativos Perú para MVP V2...")
    
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    
    collection_name = settings.qdrant_collection_profiles
    
    # Crear colección si no existe
    existing = {c.name for c in client.get_collections().collections}
    if collection_name not in existing:
        print(f"Crerando colección {collection_name}...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
        )
    
    profiles = [
        {
            "empresa": "BCP",
            "industria": "Banca",
            "area": "Operaciones",
            "objetivos": "Eficiencia operativa, automatización segura, reducción de FTEs en tareas manuales.",
            "pain_points": "Lentitud en conciliaciones, alta carga manual, riesgo de error humano.",
            "notas": "Cultura muy orientada al riesgo. Prefieren soluciones modulares y escalables, no despliegues 'big bang'. Muy formales."
        },
        {
            "empresa": "Alicorp",
            "industria": "Consumo Masivo",
            "area": "Supply Chain",
            "objetivos": "Optimización de inventarios, reducción de tiempos de despacho, visibilidad en tiempo real.",
            "pain_points": "Desconexión entre almacenes y ventas, falta de predicción de demanda.",
            "notas": "Foco extremo en el ROI y el margen. Buscan soluciones que impacten directamente en el Ebitda. Ágiles en la toma de decisiones."
        },
        {
            "empresa": "Interbank",
            "industria": "Banca",
            "area": "Innovación",
            "objetivos": "Ser el banco más ágil del Perú, mejorar NPS digital, atraer talento joven.",
            "pain_points": "Fricción en el onboarding digital, competencia con fintechs.",
            "notas": "Cultura de innovación abierta. Les gusta probar tecnologías disruptivas (GenAI). Valoran la rapidez sobre la perfección absoluta."
        },
        {
            "empresa": "BBVA",
            "industria": "Banca",
            "area": "Operaciones",
            "objetivos": "Globalización de procesos, cumplimiento regulatorio estricto, digitalización total.",
            "pain_points": "Sistemas legacy complejos, regulaciones de compliance pesadas.",
            "notas": "Procesos de aprobación globales. Buscan estandarización y cumplimiento normativo impecable."
        },
        {
            "empresa": "Supermercados Peruanos",
            "industria": "Retail",
            "area": "Operaciones",
            "objetivos": "Reducir mermas, optimizar turnos de personal, mejorar experiencia en caja.",
            "pain_points": "Alta rotación de personal, ineficiencia en gestión de perecederos.",
            "notas": "Márgenes muy ajustados. Buscan soluciones prácticas y de bajo mantenimiento que el personal de tienda pueda usar sin fricción."
        }
    ]
    
    points = []
    for p in profiles:
        point_id = hashlib.md5(f"{p['empresa']}-{p['area']}".lower().encode()).hexdigest()
        points.append(
            models.PointStruct(
                id=point_id,
                vector=[0.0] * 768, # Vector dummy
                payload=p
            )
        )
        
    client.upsert(collection_name=collection_name, points=points)
    print(f"✅ Se han sembrado {len(profiles)} perfiles corporativos con éxito.")

if __name__ == "__main__":
    try:
        seed_profiles()
    except Exception as e:
        print(f"❌ Error en la siembra: {e}")
