"""
seed_v4_data.py — Script maestro para poblar toda la data del backend NEO V4.

Ejecuta:
  cd backend
  python -m scripts.seed_v4_data

Pasos:
  1. Carga CSVs (neo_legacy.csv + ai_cases.csv) a Qdrant Cloud
  2. Crea perfiles de los 12 clientes priorizados en SQLite
  3. Crea inteligencia sectorial (radiografias de industria) en SQLite
  4. Crea human insights de ejemplo en SQLite
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("seed_v4")


# ── Step 1: Load CSVs to Qdrant ─────────────────────────────────────────────

def seed_cases_to_qdrant() -> None:
    logger.info("=== STEP 1: Loading CSVs to Qdrant Cloud ===")
    from src.tools.qdrant_tool import db_connection
    from src.config import get_settings

    settings = get_settings()
    collection = settings.qdrant_collection_cases
    logger.info(f"Target collection: {collection}")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")

    # Find CSVs in project root /data/
    data_dir = Path(__file__).resolve().parents[2] / "data"
    csv_files = sorted(str(p) for p in data_dir.glob("*.csv"))

    if not csv_files:
        logger.error(f"No CSVs found in {data_dir}")
        return

    logger.info(f"Found {len(csv_files)} CSV files: {[Path(f).name for f in csv_files]}")

    result = db_connection.load_csv_files(csv_files, collection_name=collection)
    logger.info(f"Ingestion result: {json.dumps(result, indent=2, default=str)}")


# ── Step 2: Seed company profiles ────────────────────────────────────────────

COMPANY_PROFILES = [
    {
        "company_id": "BCP",
        "area": "Operaciones",
        "profile_payload": {
            "nombre": "Banco de Credito del Peru",
            "sector": "Banca",
            "empleados_ti": "~3,200",
            "revenue_anual": "S/. 12,400M",
            "presupuesto_tech": "~USD 180M",
            "prioridades_estrategicas": [
                "Transformacion digital de canales",
                "Hiperpersonalizacion de ofertas con IA",
                "Reduccion de costos operativos via automatizacion"
            ],
            "pain_points": [
                "Fuga de clientes premium al 12% anual",
                "Tiempo de evaluacion crediticia PYME excesivo (5 dias)",
                "Silos de datos entre canales dificultan la vision 360"
            ],
            "decision_makers": [
                {"nombre": "VP Innovacion Digital", "departamento": "TI"},
                {"nombre": "Gerente de Analitica Avanzada", "departamento": "Marketing"}
            ],
            "stack_actual": ["AWS", "Kubernetes", "Python", "Tableau", "Kafka"],
            "satisfaccion_nps": 62,
            "proyectos_activos": 14,
        }
    },
    {
        "company_id": "INTERBANK",
        "area": "Customer Experience",
        "profile_payload": {
            "nombre": "Interbank",
            "sector": "Banca",
            "empleados_ti": "~1,800",
            "revenue_anual": "S/. 5,200M",
            "presupuesto_tech": "~USD 95M",
            "prioridades_estrategicas": [
                "Experiencia digital sin friccion",
                "Banca conversacional 24/7 con IA",
                "Expansion de creditos personales via scoring alternativo"
            ],
            "pain_points": [
                "800K consultas mensuales saturan call center",
                "CSAT de apenas 62% en canales tradicionales",
                "Comunicaciones genericas (open rate 8%)"
            ],
            "decision_makers": [
                {"nombre": "Chief Digital Officer", "departamento": "Innovacion"},
                {"nombre": "Head of Customer Experience", "departamento": "CX"}
            ],
            "stack_actual": ["Azure", "Docker", "MongoDB", "React", "LangChain"],
            "satisfaccion_nps": 58,
            "proyectos_activos": 9,
        }
    },
    {
        "company_id": "BBVA",
        "area": "Operaciones",
        "profile_payload": {
            "nombre": "BBVA Peru",
            "sector": "Banca",
            "empleados_ti": "~2,100",
            "revenue_anual": "S/. 4,800M",
            "presupuesto_tech": "~USD 110M",
            "prioridades_estrategicas": [
                "Prevencion de fraude transaccional en tiempo real",
                "Automatizacion de procesos back-office con RPA",
                "Open Banking y APIs para ecosistema fintech"
            ],
            "pain_points": [
                "USD 3.2M perdidos anuales por fraude en tarjetas",
                "12,000 horas-hombre en tareas repetitivas back-office",
                "65% de falsos positivos en sistema de fraude actual"
            ],
            "decision_makers": [
                {"nombre": "Director de Riesgos", "departamento": "Riesgos"},
                {"nombre": "VP de Operaciones", "departamento": "Operaciones"}
            ],
            "stack_actual": ["TensorFlow", "UiPath", "SQL Server", "Kafka", "Kubernetes"],
            "satisfaccion_nps": 55,
            "proyectos_activos": 11,
        }
    },
    {
        "company_id": "ALICORP",
        "area": "Operaciones",
        "profile_payload": {
            "nombre": "Alicorp",
            "sector": "Consumo Masivo",
            "empleados_ti": "~800",
            "revenue_anual": "S/. 13,500M",
            "presupuesto_tech": "~USD 45M",
            "prioridades_estrategicas": [
                "Optimizacion de cadena de suministro con IA",
                "Inteligencia de trade marketing en punto de venta",
                "Forecast de demanda a nivel SKU-tienda"
            ],
            "pain_points": [
                "Error de forecast del 25% genera sobrestock y quiebres",
                "3.8% de ventas netas perdidas por ineficiencia de inventario",
                "ROI de trade marketing no medible por canal"
            ],
            "decision_makers": [
                {"nombre": "VP Supply Chain", "departamento": "Operaciones"},
                {"nombre": "Director de Inteligencia Comercial", "departamento": "Marketing"}
            ],
            "stack_actual": ["Databricks", "Snowflake", "Power BI", "Python", "SAP"],
            "satisfaccion_nps": 72,
            "proyectos_activos": 6,
        }
    },
    {
        "company_id": "RIMAC",
        "area": "Operaciones",
        "profile_payload": {
            "nombre": "Rimac Seguros",
            "sector": "Seguros",
            "empleados_ti": "~650",
            "revenue_anual": "S/. 6,800M (primas)",
            "presupuesto_tech": "~USD 35M",
            "prioridades_estrategicas": [
                "Automatizacion de procesamiento de siniestros",
                "Modelos actuariales mejorados con ML",
                "Experiencia digital del asegurado"
            ],
            "pain_points": [
                "Siniestralidad vehicular alta (75% en segmento jovenes)",
                "72 horas promedio para procesar siniestro vehicular",
                "Deteccion de fraude reactiva (solo 15% detectado)"
            ],
            "decision_makers": [
                {"nombre": "CTO", "departamento": "TI"},
                {"nombre": "Director Actuarial", "departamento": "Finanzas"}
            ],
            "stack_actual": ["AWS", "Python", "PyTorch", "FastAPI", "React Native"],
            "satisfaccion_nps": 65,
            "proyectos_activos": 8,
        }
    },
    {
        "company_id": "PACIFICO",
        "area": "Operaciones",
        "profile_payload": {
            "nombre": "Pacifico Seguros",
            "sector": "Seguros",
            "empleados_ti": "~500",
            "revenue_anual": "S/. 5,100M (primas)",
            "presupuesto_tech": "~USD 28M",
            "prioridades_estrategicas": [
                "Deteccion proactiva de fraude en salud",
                "Digitalizacion del journey del asegurado",
                "Reduccion de costos operativos con automatizacion"
            ],
            "pain_points": [
                "Solo 15% de fraudes en salud detectados",
                "8 analistas manuales revisando reclamos",
                "S/. 8M anuales perdidos por fraude no detectado"
            ],
            "decision_makers": [
                {"nombre": "Gerente de Innovacion", "departamento": "Innovacion"},
                {"nombre": "VP de Operaciones de Salud", "departamento": "Operaciones"}
            ],
            "stack_actual": ["Neo4j", "Python", "Docker", "FastAPI", "PostgreSQL"],
            "satisfaccion_nps": 60,
            "proyectos_activos": 5,
        }
    },
    {
        "company_id": "SCOTIABANK",
        "area": "TI",
        "profile_payload": {
            "nombre": "Scotiabank Peru",
            "sector": "Banca",
            "empleados_ti": "~1,400",
            "revenue_anual": "S/. 3,200M",
            "presupuesto_tech": "~USD 72M",
            "prioridades_estrategicas": [
                "Open Banking y monetizacion de APIs",
                "Seguridad de datos y cumplimiento regulatorio",
                "Modernizacion de core bancario"
            ],
            "pain_points": [
                "Cumplimiento de regulacion Open Banking SBS",
                "Ecosistema fintech creciendo sin estrategia de APIs",
                "Legacy core bancario dificulta innovacion agil"
            ],
            "decision_makers": [
                {"nombre": "CIO", "departamento": "TI"},
                {"nombre": "Director de Banca Digital", "departamento": "Innovacion"}
            ],
            "stack_actual": ["Kong", "OAuth 2.0", "Redis", "Python", "Kubernetes"],
            "satisfaccion_nps": 52,
            "proyectos_activos": 7,
        }
    },
    {
        "company_id": "MIBANCO",
        "area": "Finanzas",
        "profile_payload": {
            "nombre": "MiBanco",
            "sector": "Banca",
            "empleados_ti": "~400",
            "revenue_anual": "S/. 3,800M",
            "presupuesto_tech": "~USD 22M",
            "prioridades_estrategicas": [
                "Inclusion financiera con scoring alternativo",
                "Digitalizacion del proceso de microfinanzas",
                "Automatizacion de cobranza inteligente"
            ],
            "pain_points": [
                "60% de solicitantes sin historial crediticio tradicional",
                "Rechazo sistematico de buenos clientes no bancarizados",
                "Procesos de evaluacion crediticia mayormente manuales"
            ],
            "decision_makers": [
                {"nombre": "Gerente de Riesgo Crediticio", "departamento": "Finanzas"},
                {"nombre": "Director de Inclusion Financiera", "departamento": "Comercial"}
            ],
            "stack_actual": ["AWS", "Scikit-learn", "Python", "Hive", "Tableau"],
            "satisfaccion_nps": 70,
            "proyectos_activos": 4,
        }
    },
    {
        "company_id": "CREDICORP",
        "area": "Finanzas",
        "profile_payload": {
            "nombre": "Credicorp",
            "sector": "Banca",
            "empleados_ti": "~5,000 (grupo)",
            "revenue_anual": "S/. 22,000M (grupo)",
            "presupuesto_tech": "~USD 320M (grupo)",
            "prioridades_estrategicas": [
                "Vision unificada de riesgo corporativo multi-subsidiaria",
                "Plataforma centralizada de datos y analitica",
                "Compliance de Basilea III y regulacion SBS"
            ],
            "pain_points": [
                "4 subsidiarias con sistemas heterogeneos",
                "Reportes de riesgo consolidados toman 5 dias",
                "Sin vision 360 de exposure por grupo economico"
            ],
            "decision_makers": [
                {"nombre": "Chief Risk Officer (Grupo)", "departamento": "Riesgos"},
                {"nombre": "CTO Corporativo", "departamento": "TI"}
            ],
            "stack_actual": ["Databricks", "Delta Lake", "Spark", "Python", "Angular"],
            "satisfaccion_nps": 68,
            "proyectos_activos": 12,
        }
    },
    {
        "company_id": "PLAZA VEA",
        "area": "Comercial",
        "profile_payload": {
            "nombre": "Plaza Vea (Supermercados Peruanos)",
            "sector": "Retail",
            "empleados_ti": "~350",
            "revenue_anual": "S/. 7,200M",
            "presupuesto_tech": "~USD 18M",
            "prioridades_estrategicas": [
                "Pricing dinamico basado en elasticidad de demanda",
                "Personalizacion de experiencia en e-commerce",
                "Optimizacion de merma y cadena de frio"
            ],
            "pain_points": [
                "50,000+ SKUs con precios actualizados manualmente",
                "Sin considerar elasticidad de demanda ni competencia",
                "Merma por sobre-stock alcanza el 4.2% de ventas"
            ],
            "decision_makers": [
                {"nombre": "Director Comercial", "departamento": "Comercial"},
                {"nombre": "Gerente de BI y Analitica", "departamento": "TI"}
            ],
            "stack_actual": ["PostgreSQL", "Python", "React", "Docker", "Kafka"],
            "satisfaccion_nps": 58,
            "proyectos_activos": 5,
        }
    },
    {
        "company_id": "FALABELLA",
        "area": "Marketing",
        "profile_payload": {
            "nombre": "Falabella Peru",
            "sector": "Retail",
            "empleados_ti": "~600",
            "revenue_anual": "S/. 4,500M",
            "presupuesto_tech": "~USD 32M",
            "prioridades_estrategicas": [
                "Recomendador de productos omnicanal con ML",
                "Unificacion de experiencia web-app-tienda",
                "Loyalty program analytics y personalizacion"
            ],
            "pain_points": [
                "Conversion digital 1.8% vs benchmark regional 3.2%",
                "Recomendaciones genericas sin contexto de usuario",
                "Datos de cliente fragmentados entre canales"
            ],
            "decision_makers": [
                {"nombre": "Head of e-Commerce", "departamento": "Marketing"},
                {"nombre": "Director de Data & Analytics", "departamento": "TI"}
            ],
            "stack_actual": ["BigQuery", "TensorFlow", "Redis", "FastAPI", "Kubernetes"],
            "satisfaccion_nps": 55,
            "proyectos_activos": 7,
        }
    },
    {
        "company_id": "SODIMAC",
        "area": "Operaciones",
        "profile_payload": {
            "nombre": "Sodimac Peru",
            "sector": "Retail",
            "empleados_ti": "~280",
            "revenue_anual": "S/. 3,800M",
            "presupuesto_tech": "~USD 15M",
            "prioridades_estrategicas": [
                "Optimizacion de logistica ultima milla",
                "Experiencia omnicanal de compra y entrega",
                "Prediccion de demanda para productos estacionales"
            ],
            "pain_points": [
                "18% de entregas fuera de ventana horaria",
                "NPS de delivery de apenas 55",
                "Costos de ultima milla crecientes y no optimizados"
            ],
            "decision_makers": [
                {"nombre": "Director de Logistica", "departamento": "Operaciones"},
                {"nombre": "Gerente de Digital Commerce", "departamento": "Comercial"}
            ],
            "stack_actual": ["Google Maps API", "Python", "OR-Tools", "React", "FastAPI"],
            "satisfaccion_nps": 55,
            "proyectos_activos": 4,
        }
    },
]


INDUSTRY_RADIOGRAPHIES = [
    {
        "industry_target": "Banca",
        "profile_payload": {
            "executive_summary": "El sector bancario peruano esta en plena transformacion digital impulsada por regulacion Open Banking de la SBS, competencia agresiva de fintechs como Yape y Plin, y demanda creciente de experiencias digitales hiperpersonalizadas. La inversion en IA y ML se ha duplicado en 2025, con foco en prevencion de fraude, scoring alternativo para inclusion financiera, y automatizacion de procesos back-office. Los bancos que no aceleren su adopcion tecnologica enfrentan riesgo de desintermediacion.",
            "tendencias": [
                "Open Banking regulado por SBS entra en vigor 2026",
                "IA generativa para atencion al cliente 24/7",
                "Scoring alternativo para inclusion financiera",
                "Automatizacion RPA de procesos back-office",
                "Hiperpersonalizacion con datos transaccionales"
            ],
            "oportunidades": [
                "USD 500M en mercado desatendido de microfinanzas digitales",
                "Reduccion de hasta 40% en costos operativos via automatizacion",
                "Cross-sell revenue con modelos de propension basados en ML"
            ],
            "benchmarks_regionales": [
                "Nubank: 100M clientes con CAC de USD 7 vs USD 100 promedio",
                "Itau: Reduccion 50% en tiempo de aprobacion crediticia con ML",
                "Mercado Pago: Crecimiento 340% en cartera de creditos digitales"
            ]
        },
        "triggers_payload": [
            {
                "trigger_type": "new_law",
                "title": "SBS publica norma de Open Banking para 2026",
                "rationale": "Obliga a todos los bancos a exponer APIs financieras estandarizadas",
                "severity": "high"
            },
            {
                "trigger_type": "analyst_alert",
                "title": "Fintechs capturan 15% de pagos digitales en Peru",
                "rationale": "Yape y Plin superan 25M de usuarios activos mensuales",
                "severity": "medium"
            },
            {
                "trigger_type": "budget_shift",
                "title": "Presupuesto TI bancario crece 22% para 2026",
                "rationale": "Mayor inversion en cloud, IA y ciberseguridad",
                "severity": "medium"
            }
        ]
    },
    {
        "industry_target": "Seguros",
        "profile_payload": {
            "executive_summary": "La industria de seguros en Peru vive un momento de disrupcion con la adopcion de computer vision para siniestros, modelos actuariales basados en ML, y deteccion de fraude con graph neural networks. La penetracion de seguros en Peru es apenas 1.8% del PBI (vs 3.5% regional), lo que representa una oportunidad masiva de crecimiento para aseguradoras que digitalicen sus procesos y mejoren la experiencia del cliente.",
            "tendencias": [
                "Computer vision para procesamiento automatico de siniestros",
                "Telemetria vehicular para pricing personalizado",
                "Microseguros digitales para segmentos no atendidos",
                "Deteccion de fraude con grafos de relaciones",
                "Experiencia digital end-to-end del asegurado"
            ],
            "oportunidades": [
                "Gap de penetracion de 1.7 puntos del PBI vs promedio regional",
                "S/. 2,000M en mercado potencial de microseguros",
                "30% de reduccion posible en siniestralidad con modelos ML"
            ],
            "benchmarks_regionales": [
                "Lemonade: Pago de siniestro en 3 segundos con IA",
                "SulAmerica Brasil: -35% fraude con graph analytics",
                "Sura Colombia: +25 pts NPS con app de auto-gestion digital"
            ]
        },
        "triggers_payload": [
            {
                "trigger_type": "new_law",
                "title": "SBS flexibiliza regulacion para microseguros digitales",
                "rationale": "Permite polizas 100% digitales sin presencia fisica",
                "severity": "high"
            },
            {
                "trigger_type": "analyst_alert",
                "title": "Fraude en seguros de salud crece 18% en Peru",
                "rationale": "Mayor sofisticacion de redes de fraude organizadas",
                "severity": "high"
            }
        ]
    },
    {
        "industry_target": "Retail",
        "profile_payload": {
            "executive_summary": "El retail peruano comienza su transicion agresiva al omnicanal con e-commerce creciendo 35% anual. Los players principales (Plaza Vea, Falabella, Sodimac) invierten fuertemente en logistica ultima milla, pricing dinamico y personalizacion de experiencia. La data del punto de venta y el comportamiento digital se convierten en el diferenciador competitivo clave.",
            "tendencias": [
                "Pricing dinamico basado en elasticidad y competencia",
                "Quick commerce y optimizacion de ultima milla",
                "Recomendadores con embeddings de producto y sesion",
                "Loyalty analytics con modelos de churn prediction",
                "Automatizacion de cadena de frio y merma"
            ],
            "oportunidades": [
                "E-commerce Peru crece 35% anual con penetracion del 12%",
                "USD 200M en ahorro potencial por optimizacion de ultima milla",
                "Incremento de ticket promedio de 15-25% con recomendadores ML"
            ],
            "benchmarks_regionales": [
                "Mercado Libre: Entrega same-day en 85% de ordenes urbanas",
                "Rappi: Optimizacion de ruta reduce costo por entrega en 28%",
                "Cencosud Chile: +2.3pp de margen con pricing dinamico"
            ]
        },
        "triggers_payload": [
            {
                "trigger_type": "stock_drop",
                "title": "InRetail reporta caida de margenes en Q3 2025",
                "rationale": "Presion competitiva de e-commerce pure players",
                "severity": "medium"
            },
            {
                "trigger_type": "budget_shift",
                "title": "Retailers peruanos duplican inversion en logistica tech",
                "rationale": "Foco en dark stores, ruteo inteligente y tracking en tiempo real",
                "severity": "medium"
            }
        ]
    },
    {
        "industry_target": "Consumo Masivo",
        "profile_payload": {
            "executive_summary": "Las empresas de consumo masivo en Peru enfrentan presion de margenes por inflacion de insumos y competencia de marcas propias del retail. La IA se posiciona como diferenciador para optimizar supply chain, mejorar la ejecucion en punto de venta, y personalizar estrategias de trade marketing por canal y categoria. Alicorp lidera la transformacion digital del sector.",
            "tendencias": [
                "Demand forecasting a nivel SKU-tienda con ML",
                "Trade marketing intelligence con datos de sell-out",
                "Automatizacion de planificacion de produccion",
                "Revenue growth management con analisis de price-pack",
                "Datos de sell-out POS para decision real-time"
            ],
            "oportunidades": [
                "Reduccion del 15-25% en error de forecast con modelos ensemble",
                "USD 50M en ahorro de inventario por optimizacion de supply chain",
                "ROI de trade marketing mejorable en 25-30% con analytics"
            ],
            "benchmarks_regionales": [
                "Unilever Mexico: Forecast accuracy mejoro de 72% a 91% con IA",
                "AB InBev Brasil: Revenue management con IA genera +3% revenue",
                "Nestle Region: Planificacion de produccion automatizada reduce waste 22%"
            ]
        },
        "triggers_payload": [
            {
                "trigger_type": "stock_drop",
                "title": "Presion de margenes por inflacion de insumos en 2025",
                "rationale": "Costos de commodities agroindustriales suben 12%",
                "severity": "medium"
            },
            {
                "trigger_type": "analyst_alert",
                "title": "Marcas propias de retailers ganan 3pp de market share",
                "rationale": "Consumidores migran a opciones de mejor value-for-money",
                "severity": "high"
            }
        ]
    },
]


HUMAN_INSIGHTS = [
    {
        "company_id": "BCP",
        "author": "Carlos Mendoza",
        "raw_text": "En la reunion con el VP de Innovacion Digital del BCP, nos confirmaron que la fuga de clientes premium es su dolor numero uno. Estan perdiendo S/. 45M anuales y su modelo actual de retencion solo detecta clientes en riesgo cuando ya es tarde. Necesitan un modelo predictivo con al menos 30 dias de anticipacion. El decision maker es el VP de Innovacion y tiene presupuesto aprobado para Q1 2026.",
        "source": "reunion_comercial"
    },
    {
        "company_id": "BCP",
        "author": "Ana Torres",
        "raw_text": "El equipo de evaluacion crediticia PYME del BCP esta frustrado. El proceso toma 5 dias y rechazan el 40% de solicitudes solo porque falta documentacion. Quieren automatizar con OCR e IA para reducir a horas. El Gerente de Banca PYME esta urgido.",
        "source": "reunion_comercial"
    },
    {
        "company_id": "INTERBANK",
        "author": "Jose Paredes",
        "raw_text": "Interbank recibe mas de 800K consultas mensuales en su call center. El tiempo de espera es de 8 minutos y el CSAT esta en 62%. El Chief Digital Officer quiere un chatbot con LLM que resuelva al menos el 70% de consultas sin agente humano. Tienen presupuesto de USD 2M aprobado.",
        "source": "reunion_comercial"
    },
    {
        "company_id": "ALICORP",
        "author": "Maria Gutierrez",
        "raw_text": "El VP de Supply Chain de Alicorp esta preocupado por las perdidas de 3.8% de ventas netas por quiebres y sobrestock. Su forecast manual tiene error del 25%. Necesitan demand forecasting con ML a nivel SKU-tienda urgente. Hablan de un proyecto de USD 1.5M.",
        "source": "reunion_comercial"
    },
    {
        "company_id": "RIMAC",
        "author": "Roberto Diaz",
        "raw_text": "El CTO de Rimac nos conto que procesan siniestros vehiculares en 72 horas promedio y eso destruye el NPS. Quieren computer vision para que el asegurado envie fotos y el sistema autorice taller en horas. Tienen un piloto aprobado para Q2 2026 con presupuesto de USD 800K.",
        "source": "reunion_comercial"
    },
    {
        "company_id": "PLAZA VEA",
        "author": "Laura Vargas",
        "raw_text": "El Director Comercial de Plaza Vea mencionó que manejan 50K SKUs con precios manuales y sin considerar elasticidad ni competencia. Pierden margen por no tener pricing dinámico. Quieren implementar un motor de pricing con IA para el primer semestre 2026.",
        "source": "reunion_comercial"
    },
]


def seed_profiles_to_sqlite() -> None:
    logger.info("=== STEP 2: Seeding company profiles to SQLite ===")
    from src.services.intel_storage import company_profile_repository

    for profile in COMPANY_PROFILES:
        company_id = profile["company_id"]
        area = profile["area"]
        payload = profile["profile_payload"]

        try:
            company_profile_repository.upsert_profile(
                company_id=company_id,
                area=area,
                profile_payload=payload,
            )
            logger.info(f"  Profile seeded: {company_id} / {area}")
        except Exception as exc:
            logger.error(f"  Failed to seed profile {company_id}: {exc}")

    logger.info(f"  Total profiles seeded: {len(COMPANY_PROFILES)}")


def seed_industry_radar_to_sqlite() -> None:
    logger.info("=== STEP 3: Seeding industry radiographies to SQLite ===")
    from src.services.intel_storage import industry_radar_repository

    for radiography in INDUSTRY_RADIOGRAPHIES:
        industry = radiography["industry_target"]
        try:
            industry_radar_repository.upsert_radiography(
                industry_target=industry,
                profile_payload=radiography["profile_payload"],
                triggers_payload=radiography["triggers_payload"],
            )
            logger.info(f"  Industry seeded: {industry}")
        except Exception as exc:
            logger.error(f"  Failed to seed industry {industry}: {exc}")

    logger.info(f"  Total industries seeded: {len(INDUSTRY_RADIOGRAPHIES)}")


def seed_human_insights_to_sqlite() -> None:
    logger.info("=== STEP 4: Seeding human insights to SQLite ===")
    from src.services.intel_storage import human_insight_repository
    from src.services.human_insight_parser import parse_sales_insight_text

    for insight_data in HUMAN_INSIGHTS:
        company_id = insight_data["company_id"]
        author = insight_data["author"]
        raw_text = insight_data["raw_text"]
        source = insight_data["source"]

        try:
            # Try to parse with LLM, fallback internally
            parsed = parse_sales_insight_text(raw_text)

            human_insight_repository.save(
                company_id=company_id,
                author=author,
                department=parsed.department,
                sentiment=parsed.sentiment,
                raw_text=raw_text,
                structured_payload=parsed.structured_payload,
                source=source,
            )
            logger.info(f"  Insight seeded: {company_id} by {author} -> {parsed.department}")
        except Exception as exc:
            logger.error(f"  Failed to seed insight for {company_id}: {exc}")

    logger.info(f"  Total insights seeded: {len(HUMAN_INSIGHTS)}")


def main() -> None:
    logger.info("=" * 60)
    logger.info("NEO V4 — Data Seed Script")
    logger.info("=" * 60)

    # Step 1: Cases to Qdrant
    try:
        seed_cases_to_qdrant()
    except Exception as exc:
        logger.error(f"Step 1 failed: {exc}")
        logger.info("Continuing with remaining steps...")

    # Step 2: Profiles to SQLite
    try:
        seed_profiles_to_sqlite()
    except Exception as exc:
        logger.error(f"Step 2 failed: {exc}")

    # Step 3: Industry radiographies to SQLite
    try:
        seed_industry_radar_to_sqlite()
    except Exception as exc:
        logger.error(f"Step 3 failed: {exc}")

    # Step 4: Human insights to SQLite
    try:
        seed_human_insights_to_sqlite()
    except Exception as exc:
        logger.error(f"Step 4 failed: {exc}")

    logger.info("=" * 60)
    logger.info("SEED COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
