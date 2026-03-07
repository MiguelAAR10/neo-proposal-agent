"""Seed script: populates SQLite with realistic demo data for profiles, insights, and sector radiographies.

Usage:
    cd backend && python -m src.tools.seed_demo_data

Data created:
- Company profiles for all 12 prioritized clients across key areas
- Human insights (sales notes) for top 6 clients
- Industry radiographies for: Banca, Seguros, Consumo masivo, Retail, Microfinanzas, Servicios financieros
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ensure project root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import get_settings
from src.services.intel_storage import (
    company_profile_repository,
    human_insight_repository,
    industry_radar_repository,
)
from src.models.human_insight import StructuredInsightItem


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _days_ago(days: int) -> str:
    return (_now() - timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# 1. COMPANY PROFILES — realistic data for Peruvian enterprise demo
# ---------------------------------------------------------------------------
COMPANY_PROFILES = [
    # BANCA
    {
        "company_id": "BCP",
        "area": "Operaciones",
        "profile_payload": {
            "empresa": "BCP",
            "area": "Operaciones",
            "industria": "Banca",
            "objetivos": [
                "Reducir tiempo de conciliación bancaria de 4h a <30min diarias",
                "Automatizar 80% de procesos manuales de back-office para 2026",
                "Eliminar errores en reconciliación interbancaria (meta: <0.1% error rate)",
            ],
            "pain_points": [
                "Conciliación manual consume 4-5 horas diarias con 3% de errores",
                "Dependencia de 12 analistas dedicados a procesos repetitivos",
                "Falta de trazabilidad regulatoria en operaciones manuales",
                "Tiempo de respuesta a SBS excede 48h por extracción manual de datos",
            ],
            "decision_makers": [
                "Gianfranco Ferrari - CEO",
                "Diego Cavero - VP de Operaciones y Tecnología",
                "María Elena Vásquez - Directora de Transformación Digital",
            ],
            "sentimiento_comercial": "Urgente",
            "notas": "BCP es el banco más grande del Perú con alta apertura a innovación tecnológica. Cultura orientada a resultados, priorizan quick wins con ROI demostrable. Restricciones regulatorias de SBS son factor clave.",
            "kpis": {
                "revenue": "S/. 8,200M",
                "satisfaction": "NPS 62",
                "empleados_ti": "1,200+",
                "proyectos": "45 activos",
            },
        },
    },
    {
        "company_id": "BCP",
        "area": "Marketing",
        "profile_payload": {
            "empresa": "BCP",
            "area": "Marketing",
            "industria": "Banca",
            "objetivos": [
                "Incrementar conversión de campañas digitales en 35%",
                "Reducir CPL (Cost per Lead) de canales digitales en 20%",
                "Personalizar ofertas para los 15M+ de clientes activos",
            ],
            "pain_points": [
                "Segmentación de clientes basada en reglas estáticas, no predictivas",
                "Campañas genéricas generan fatiga publicitaria",
                "Falta de atribución cross-channel precisa",
            ],
            "decision_makers": [
                "Francesca Raffo - VP de Marketing y Experiencia",
                "Carlos Merino - Director de Marketing Digital",
            ],
            "sentimiento_comercial": "Positivo",
            "notas": "Alto interés en IA para personalización. Presupuesto aprobado para pilotos.",
        },
    },
    {
        "company_id": "INTERBANK",
        "area": "Operaciones",
        "profile_payload": {
            "empresa": "INTERBANK",
            "area": "Operaciones",
            "industria": "Banca",
            "objetivos": [
                "Migrar 60% de procesos de backoffice a automatización inteligente",
                "Reducir SLA de atención de reclamos de 15 a 5 días hábiles",
                "Digitalizar 100% del onboarding de productos bancarios",
            ],
            "pain_points": [
                "Procesos de backoffice fragmentados entre 5 sistemas legacy",
                "Tiempos de respuesta a clientes fuera de SLA en 30% de casos",
                "Alta rotación en equipo operativo por tareas repetitivas",
            ],
            "decision_makers": [
                "Carlos Rodríguez-Pastor - CEO",
                "Luis Felipe Castellanos - CEO Interbank",
                "Michela Casassa - VP Transformación Digital",
            ],
            "sentimiento_comercial": "Positivo",
            "notas": "Interbank tiene cultura de innovación más ágil que otros bancos peruanos. Lideraron banca digital con app Tunki.",
            "kpis": {
                "revenue": "S/. 4,100M",
                "satisfaction": "NPS 58",
                "empleados_ti": "800+",
                "proyectos": "32 activos",
            },
        },
    },
    {
        "company_id": "BBVA",
        "area": "Operaciones",
        "profile_payload": {
            "empresa": "BBVA",
            "area": "Operaciones",
            "industria": "Banca",
            "objetivos": [
                "Optimizar modelos de credit scoring con 15% más de precisión",
                "Reducir fraude transaccional en 40% mediante detección en tiempo real",
                "Escalar analítica de riesgo a portafolio completo",
            ],
            "pain_points": [
                "Modelos de scoring actuales basados en reglas tienen alta tasa de falsos positivos",
                "Detección de fraude reactiva, no preventiva",
                "Cumplimiento regulatorio genera overhead de 20% en operaciones",
            ],
            "decision_makers": [
                "Fernando Eguiluz - CEO BBVA Perú",
                "Alberto Delgado - Director de Riesgos",
            ],
            "sentimiento_comercial": "Riesgo",
            "notas": "BBVA Perú sigue lineamientos globales de BBVA España. Decisiones de tech pasan por Madrid en casos grandes. Empresa conservadora en adopción tecnológica.",
            "kpis": {
                "revenue": "S/. 3,800M",
                "satisfaction": "NPS 51",
                "empleados_ti": "650+",
                "proyectos": "28 activos",
            },
        },
    },
    {
        "company_id": "ALICORP",
        "area": "Supply Chain",
        "profile_payload": {
            "empresa": "ALICORP",
            "area": "Supply Chain",
            "industria": "Consumo masivo",
            "objetivos": [
                "Mejorar precisión de forecast de demanda a >90% por SKU",
                "Reducir merma y desperdicio en 25% a nivel nacional",
                "Optimizar inventario rotativo para bajar capital de trabajo en S/.50M",
            ],
            "pain_points": [
                "Forecast de demanda con 65% de precisión por SKU/tienda",
                "Merma de productos perecibles de 8% vs benchmark de 3%",
                "12 centros de distribución con niveles de stock no optimizados",
                "Planificación en Excel avanzado, no en herramientas especializadas",
            ],
            "decision_makers": [
                "Alfredo Pérez Gubbins - CEO",
                "Paola Ruchman - VP de Supply Chain",
                "Diego Torres - Director de Innovación y Data",
            ],
            "sentimiento_comercial": "Urgente",
            "notas": "Alicorp es el grupo de consumo masivo más grande del Perú. Muy data-driven pero con legacy en planificación. Abiertos a pilotos rápidos si el ROI se demuestra en <3 meses.",
            "kpis": {
                "revenue": "S/. 12,400M",
                "satisfaction": "NPS 45",
                "empleados_ti": "350+",
                "proyectos": "18 activos",
            },
        },
    },
    {
        "company_id": "RIMAC",
        "area": "Operaciones",
        "profile_payload": {
            "empresa": "RIMAC",
            "area": "Operaciones",
            "industria": "Seguros",
            "objetivos": [
                "Automatizar 70% del procesamiento de siniestros",
                "Reducir tiempo de resolución de reclamos de 30 a 7 días",
                "Implementar detección de fraude en siniestros con IA",
            ],
            "pain_points": [
                "Procesamiento de siniestros 80% manual con errores frecuentes",
                "Fraude estimado en 8% de siniestros vs benchmark de 3%",
                "Documentación de pólizas dispersa entre 4 sistemas",
            ],
            "decision_makers": [
                "Lorena Martinot - CEO",
                "Carlos Valderrama - VP Operaciones",
            ],
            "sentimiento_comercial": "Urgente",
            "notas": "Rimac Seguros es la aseguradora líder del Perú. Alta urgencia en automatización por presión competitiva de insurtechs.",
            "kpis": {
                "revenue": "S/. 5,600M",
                "satisfaction": "NPS 42",
                "empleados_ti": "280+",
                "proyectos": "15 activos",
            },
        },
    },
    {
        "company_id": "PACIFICO",
        "area": "Operaciones",
        "profile_payload": {
            "empresa": "PACIFICO",
            "area": "Operaciones",
            "industria": "Seguros",
            "objetivos": [
                "Mejorar retención de cartera de pólizas en 15%",
                "Reducir tiempo de cotización y emisión de pólizas",
                "Migrar servicio al cliente a canales digitales (60% meta)",
            ],
            "pain_points": [
                "Tasa de cancelación de pólizas de 22% anual",
                "Proceso de cotización toma 48h promedio",
                "Modelo de servicio presencial costoso y poco escalable",
            ],
            "decision_makers": [
                "Javier Manzanares - CEO",
                "Alejandra Bohmer - Directora de Experiencia Cliente",
            ],
            "sentimiento_comercial": "Positivo",
            "notas": "Pacífico Seguros pertenece al grupo Credicorp. Apertura a soluciones digitales enfocadas en customer experience.",
            "kpis": {
                "revenue": "S/. 4,200M",
                "satisfaction": "NPS 48",
                "empleados_ti": "220+",
                "proyectos": "12 activos",
            },
        },
    },
    {
        "company_id": "SCOTIABANK",
        "area": "Operaciones",
        "profile_payload": {
            "empresa": "SCOTIABANK",
            "area": "Operaciones",
            "industria": "Banca",
            "objetivos": [
                "Mejorar scoring de originación crediticia con modelos ML",
                "Automatizar procesos de compliance y reportería regulatoria",
                "Incrementar cross-sell ratio de 1.8 a 2.5 productos por cliente",
            ],
            "pain_points": [
                "Scoring basado en modelos estadísticos de 2019, no actualizados",
                "Generación de reportes SBS consume 120 horas-hombre mensuales",
                "Baja tasa de cross-sell por falta de vista 360 del cliente",
            ],
            "decision_makers": [
                "Miguel Uccelli - CEO",
                "Patricia Martínez - VP de Riesgos",
            ],
            "sentimiento_comercial": "Positivo",
            "notas": "Scotiabank Perú reporta directamente a Scotiabank Canadá. Procesos de aprobación de tech siguen gobernanza global.",
            "kpis": {
                "revenue": "S/. 3,200M",
                "satisfaction": "NPS 49",
                "empleados_ti": "500+",
                "proyectos": "22 activos",
            },
        },
    },
    {
        "company_id": "MIBANCO",
        "area": "Operaciones",
        "profile_payload": {
            "empresa": "MIBANCO",
            "area": "Operaciones",
            "industria": "Microfinanzas",
            "objetivos": [
                "Automatizar evaluación crediticia de microcréditos",
                "Reducir tiempo de aprobación de crédito de 72h a 24h",
                "Equipar a 3,000 asesores de campo con herramientas digitales",
            ],
            "pain_points": [
                "Evaluación crediticia manual con formularios en papel en zonas rurales",
                "Mora de microcréditos alcanza 5.2% vs meta de 3.5%",
                "Asesores pasan 40% del tiempo en tareas administrativas",
            ],
            "decision_makers": [
                "Jorge Ramírez del Villar - CEO",
                "Claudia Ganoza - Directora de Innovación",
            ],
            "sentimiento_comercial": "Urgente",
            "notas": "MiBanco es el banco de microfinanzas más grande de Latam. Necesitan soluciones que funcionen offline/low-connectivity en zonas rurales.",
            "kpis": {
                "revenue": "S/. 2,800M",
                "satisfaction": "NPS 55",
                "empleados_ti": "180+",
                "proyectos": "10 activos",
            },
        },
    },
    {
        "company_id": "FALABELLA",
        "area": "Operaciones",
        "profile_payload": {
            "empresa": "FALABELLA",
            "area": "Operaciones",
            "industria": "Retail",
            "objetivos": [
                "Unificar experiencia omnicanal (tienda + ecommerce + app)",
                "Optimizar surtido por ubicación con analytics predictivo",
                "Reducir tiempo de fulfillment de ecommerce de 5 a 2 días",
            ],
            "pain_points": [
                "Datos de inventario desincronizados entre canales",
                "Pérdida estimada de 5% de ventas por quiebre de stock",
                "Logística last-mile costosa e ineficiente",
            ],
            "decision_makers": [
                "Gastón Sottil - CEO Falabella Perú",
                "Ana María Guzmán - Directora de Operaciones",
            ],
            "sentimiento_comercial": "Positivo",
            "notas": "Falabella Perú opera tiendas departamentales, Sodimac, y Tottus. Decisiones de inversión en tech aprobadas en Santiago.",
            "kpis": {
                "revenue": "S/. 6,800M",
                "satisfaction": "NPS 38",
                "empleados_ti": "400+",
                "proyectos": "20 activos",
            },
        },
    },
    {
        "company_id": "PLAZA VEA",
        "area": "Operaciones",
        "profile_payload": {
            "empresa": "PLAZA VEA",
            "area": "Operaciones",
            "industria": "Retail",
            "objetivos": [
                "Implementar pricing dinámico basado en competencia y demanda",
                "Reducir merma en perecibles en 30%",
                "Mejorar disponibilidad de productos en góndola a >95%",
            ],
            "pain_points": [
                "Pricing manual basado en reglas y revisiones semanales",
                "Merma en frutas y verduras de 12%, duplicando benchmark",
                "Disponibilidad en góndola de 88%, generando pérdida de ventas",
            ],
            "decision_makers": [
                "Juan Carlos Vallejo - CEO Supermercados Peruanos",
                "Roberto Seminario - VP de Operaciones",
            ],
            "sentimiento_comercial": "Urgente",
            "notas": "Plaza Vea (Supermercados Peruanos) pertenece al grupo InRetail. Competencia fuerte con Tottus y Metro ha generado urgencia en eficiencia.",
            "kpis": {
                "revenue": "S/. 7,200M",
                "satisfaction": "NPS 41",
                "empleados_ti": "180+",
                "proyectos": "14 activos",
            },
        },
    },
    {
        "company_id": "CREDICORP",
        "area": "Corporativo",
        "profile_payload": {
            "empresa": "CREDICORP",
            "area": "Corporativo",
            "industria": "Servicios financieros",
            "objetivos": [
                "Crear sinergias de datos entre BCP, Pacífico y Prima",
                "Implementar governance de datos transversal al grupo",
                "Habilitar analytics de valor unificado para el holding",
            ],
            "pain_points": [
                "Datos fragmentados entre subsidiarias sin interoperabilidad",
                "No existe vista consolidada del cliente a nivel grupo",
                "Gobierno de datos con diferentes estándares por subsidiaria",
            ],
            "decision_makers": [
                "Walter Bayly - CEO",
                "Alvaro Correa - VP de Finanzas Corporativas",
            ],
            "sentimiento_comercial": "Positivo",
            "notas": "Credicorp es el holding financiero más grande del Perú. Proyectos deben generar valor transversal entre BCP, Pacífico Seguros, Prima AFP y MiBanco.",
            "kpis": {
                "revenue": "S/. 18,500M",
                "satisfaction": "NPS N/A",
                "empleados_ti": "2,000+",
                "proyectos": "55 activos",
            },
        },
    },
    {
        "company_id": "SODIMAC",
        "area": "Operaciones",
        "profile_payload": {
            "empresa": "SODIMAC",
            "area": "Operaciones",
            "industria": "Retail",
            "objetivos": [
                "Optimizar planeamiento de inventario por categoría y tienda",
                "Mejorar productividad de asesores en tienda con herramientas digitales",
                "Reducir devoluciones de productos al 3% del volumen de ventas",
            ],
            "pain_points": [
                "Sobrestock en productos estacionales genera capital inmovilizado",
                "Asesores sin acceso a información técnica en tiempo real",
                "Devoluciones en 7% de ventas por información insuficiente al cliente",
            ],
            "decision_makers": [
                "Enrique Combe - CEO Sodimac Perú",
                "Javier Ugarte - Director de Operaciones",
            ],
            "sentimiento_comercial": "Positivo",
            "notas": "Sodimac Perú es parte del grupo Falabella pero opera con autonomía operativa local.",
            "kpis": {
                "revenue": "S/. 3,500M",
                "satisfaction": "NPS 44",
                "empleados_ti": "120+",
                "proyectos": "8 activos",
            },
        },
    },
]


# ---------------------------------------------------------------------------
# 2. INDUSTRY RADIOGRAPHIES — realistic sector intelligence
# ---------------------------------------------------------------------------
INDUSTRY_RADIOGRAPHIES = [
    {
        "industry_target": "Banca",
        "profile_payload": {
            "industria": "Banca",
            "executive_summary": "El sector bancario peruano atraviesa una transformación digital acelerada, impulsada por regulación SBS más estricta, la entrada de neobancos (Yape, Plin) y la demanda de experiencias 100% digitales. Los 4 bancos principales concentran el 83% de activos y están compitiendo en automatización de procesos, IA predictiva para riesgo, y omnicanalidad. La SBS publicó en Q4 2025 nuevos requisitos de reportería en tiempo real que obligan a modernizar infraestructura legacy.",
            "tendencias": [
                "Open Banking: SBS prepara regulación de APIs abiertas para 2026",
                "IA en credit scoring: bancos migrando de modelos scorecard a ML ensemble",
                "Automatización RPA+IA: casos de uso en conciliación, compliance y onboarding",
                "Billeteras digitales: Yape alcanzó 15M usuarios, redefiniendo pagos",
                "Ciberseguridad: SOC con IA obligatorio post-regulación 2025",
            ],
            "benchmarks": {
                "costo_transaccion_digital": "$0.15 vs $2.80 presencial",
                "tiempo_onboarding_digital": "8 min benchmark líder vs 45 min promedio",
                "tasa_automatizacion_backoffice": "40-60% en líderes regionales",
                "nps_promedio_sector": "52 puntos",
                "roi_proyectos_ia": "180-320% en primeros 18 meses",
            },
            "oportunidades": [
                "Automatización de conciliación bancaria: ahorro de 60-80% en horas-hombre",
                "Detección de fraude en tiempo real: reducción de pérdidas en 35-50%",
                "Credit scoring con ML: incremento de 12-18% en aprobaciones sin aumentar mora",
                "Chatbots inteligentes: deflexión de 45-65% de consultas de primer nivel",
            ],
        },
        "triggers_payload": [
            {
                "trigger_type": "new_law",
                "title": "SBS Resolución 2025-045: Reportería en Tiempo Real",
                "rationale": "Los bancos deben adaptar sus sistemas para entregar reportes regulatorios con latencia máxima de 4 horas, reemplazando los ciclos batch de 48h actuales.",
                "severity": "high",
                "evidence": "Resolución SBS publicada en El Peruano el 15/11/2025. Plazo de cumplimiento: junio 2026.",
            },
            {
                "trigger_type": "analyst_alert",
                "title": "McKinsey: Banca peruana rezagada en automatización vs Chile y Colombia",
                "rationale": "Según el Global Banking Report 2025 de McKinsey, los bancos peruanos tienen 28% de automatización en backoffice vs 52% en Chile. Gap de competitividad creciente.",
                "severity": "medium",
                "evidence": "McKinsey Global Banking Annual Review, Q4 2025.",
            },
            {
                "trigger_type": "budget_shift",
                "title": "Inversión en tecnología bancaria creció 23% YoY en Perú",
                "rationale": "Los presupuestos de TI de los 4 principales bancos crecieron 23% interanual, señal de apertura a nuevos proyectos de transformación digital.",
                "severity": "medium",
                "evidence": "ASBANC Informe Trimestral Q3 2025.",
            },
        ],
    },
    {
        "industry_target": "Seguros",
        "profile_payload": {
            "industria": "Seguros",
            "executive_summary": "El sector asegurador peruano, con penetración de apenas 1.9% del PBI, tiene enorme espacio de crecimiento. Las aseguradoras enfrentan desafíos en procesamiento manual de siniestros, fraude creciente y la irrupción de insurtechs. La SBS está empujando regulación de capital dinámico que exige mejor modelización de riesgos. Rimac y Pacífico dominan el mercado con 65% de primas.",
            "tendencias": [
                "Insurtechs: 12 startups activas en Perú ofreciendo microseguros digitales",
                "Siniestros automatizados: IA para evaluación y aprobación express",
                "Telemática en autos: seguros pay-per-use ganando tracción",
                "Fraude: técnicas de deep learning para detección de documentos alterados",
                "Embedded insurance: seguros integrados en plataformas de ecommerce",
            ],
            "benchmarks": {
                "tiempo_resolucion_siniestros": "25-30 días promedio vs 7 días benchmark",
                "tasa_fraude": "6-8% estimado vs 3% benchmark internacional",
                "digitalizacion_polizas": "35% digital vs 80% benchmark",
                "nps_promedio_sector": "38 puntos",
            },
            "oportunidades": [
                "Automatización de siniestros simples: reducción de 70% en tiempo de resolución",
                "Detección de fraude con computer vision: análisis de documentos y fotos",
                "Microseguros digitales: nuevo segmento de S/.500M potenciales",
                "Chatbot + WhatsApp para gestión de pólizas y FNOL (First Notice of Loss)",
            ],
        },
        "triggers_payload": [
            {
                "trigger_type": "new_law",
                "title": "SBS: Nuevos requerimientos de capital dinámico para aseguradoras",
                "rationale": "Las aseguradoras deberán implementar modelos de capital basado en riesgo más sofisticados, requiriendo capacidades analíticas avanzadas.",
                "severity": "high",
                "evidence": "Circular SBS G-184-2025. Plazo: diciembre 2026.",
            },
            {
                "trigger_type": "analyst_alert",
                "title": "Penetración de seguros en Perú es la más baja de la Alianza del Pacífico",
                "rationale": "Con 1.9% del PBI vs 3.2% en Chile y 2.8% en Colombia, existe un gap significativo que representa oportunidad de mercado de >$2B.",
                "severity": "medium",
                "evidence": "Swiss Re Sigma Report 2025, APESEG Informe Anual.",
            },
        ],
    },
    {
        "industry_target": "Consumo masivo",
        "profile_payload": {
            "industria": "Consumo masivo",
            "executive_summary": "El sector de consumo masivo en Perú está dominado por Alicorp, Gloria y Backus. La competencia por eficiencia en cadena de suministro se ha intensificado con la inflación de costos logísticos (+18% en 2025). Las empresas están priorizando forecast de demanda con IA, optimización de rutas de distribución y visibilidad end-to-end de supply chain.",
            "tendencias": [
                "Demand sensing: IA para forecast diario por SKU/punto de venta",
                "Last-mile optimization: algoritmos para reducir costo de distribución",
                "Revenue Growth Management: pricing dinámico con analytics",
                "Sostenibilidad: trazabilidad de cadena de suministro por presión de mercado",
                "D2C (Direct-to-Consumer): canales propios digitales creciendo 40% YoY",
            ],
            "benchmarks": {
                "precision_forecast": "85-92% líderes vs 65% promedio Perú",
                "merma_perecibles": "3-4% benchmark vs 8-12% Perú",
                "costo_logistico_sobre_ventas": "8-10% benchmark vs 14% Perú",
                "fill_rate": "97% benchmark vs 91% promedio",
            },
            "oportunidades": [
                "Forecast de demanda ML: precisión de 90%+ por SKU ahorra 20-30% en merma",
                "Route optimization: reducción de 15-25% en costo de distribución",
                "Trade promotion optimization: incremento de 8-12% en ROI de promociones",
                "Computer vision en planta: control de calidad automatizado",
            ],
        },
        "triggers_payload": [
            {
                "trigger_type": "budget_shift",
                "title": "Alicorp incrementó inversión en analytics 35% para 2026",
                "rationale": "La empresa anunció en su earnings call Q3 2025 que duplica su equipo de data science y destina S/.15M adicionales a proyectos de IA aplicada.",
                "severity": "high",
                "evidence": "Alicorp Earnings Call Q3 2025, BMV filing.",
            },
            {
                "trigger_type": "analyst_alert",
                "title": "Costos logísticos en Perú 40% mayores que benchmark regional",
                "rationale": "El costo logístico sobre ventas en empresas peruanas de consumo masivo es 14% vs 10% en Chile y 9% en México, creando urgencia de optimización.",
                "severity": "medium",
                "evidence": "CSCMP Annual Report 2025, análisis GS1 Perú.",
            },
        ],
    },
    {
        "industry_target": "Retail",
        "profile_payload": {
            "industria": "Retail",
            "executive_summary": "El retail peruano crece a 6% anual impulsado por el ecommerce (+35% YoY) y modernización de formatos. Los grandes retailers (Falabella, InRetail, Cencosud) están invirtiendo fuertemente en omnicanalidad, fulfillment y personalización. La competencia con marketplaces globales (Amazon, MercadoLibre) obliga a diferenciarse con experiencia y eficiencia operativa.",
            "tendencias": [
                "Omnicanalidad real: Click & Collect, Ship from Store, BOPIS",
                "Personalización: IA para recomendaciones y next-best-action",
                "Fulfillment automatizado: dark stores y micro-fulfillment centers",
                "Pricing dinámico: ajuste en tiempo real por competencia y demanda",
                "Customer Data Platform: vista 360 del cliente cross-channel",
            ],
            "benchmarks": {
                "conversion_ecommerce": "2.8% promedio vs 4.5% benchmark",
                "fulfillment_time": "4-5 días promedio vs 1-2 días benchmark",
                "disponibilidad_gondola": "88% promedio vs 97% benchmark",
                "nps_promedio": "40 puntos",
            },
            "oportunidades": [
                "Pricing dinámico: incremento de 3-5% en margen bruto",
                "Personalización predictiva: +20% en ticket promedio",
                "Optimización de inventario: reducción de 25-35% en capital de trabajo",
                "Computer vision en tienda: analytics de tráfico y planogramas",
            ],
        },
        "triggers_payload": [
            {
                "trigger_type": "analyst_alert",
                "title": "Ecommerce peruano alcanzó $12B en 2025, +35% YoY",
                "rationale": "El crecimiento acelerado del ecommerce está forzando a retailers físicos a invertir en capacidades digitales y omnicanal para mantener competitividad.",
                "severity": "high",
                "evidence": "CAPECE Informe Anual de Ecommerce Perú 2025.",
            },
        ],
    },
    {
        "industry_target": "Microfinanzas",
        "profile_payload": {
            "industria": "Microfinanzas",
            "executive_summary": "Las microfinanzas peruanas (MiBanco, Compartamos, Caja Arequipa) atienden a 8M+ de clientes en segmentos C/D/E. El desafío principal es balance entre inclusión financiera y riesgo crediticio. La digitalización avanza lento por la naturaleza offline del negocio (asesores de campo en zonas rurales). La SBS está empujando estándares de evaluación crediticia más sofisticados.",
            "tendencias": [
                "Credit scoring alternativo: datos de celular, pagos de servicios, social data",
                "Digitalización de asesores: tablets y apps offline-first para campo",
                "Green microfinance: líneas verdes con análisis de impacto ambiental",
                "Open finance: datos de múltiples entidades para mejor evaluación",
                "Biometría: identificación digital en zonas sin conectividad",
            ],
            "benchmarks": {
                "tiempo_evaluacion_credito": "48-72h vs 4h benchmark digital",
                "mora_promedio": "5-6% vs 3.5% meta",
                "costo_evaluacion": "S/.120 por evaluación vs S/.15 digital",
                "cobertura_digital": "25% de operaciones vs 60% benchmark",
            },
            "oportunidades": [
                "Credit scoring ML: reducción de mora en 1.5-2 puntos porcentuales",
                "Automatización de evaluación: de 72h a <4h con data alternativa",
                "Field app offline-first: ahorro de 30% en tiempo administrativo de asesores",
                "Collection analytics: predicción temprana de mora para acción preventiva",
            ],
        },
        "triggers_payload": [
            {
                "trigger_type": "new_law",
                "title": "SBS: Regulación de scoring alternativo para microfinanzas",
                "rationale": "La SBS habilitará uso de datos alternativos en evaluación crediticia, abriendo la puerta a modelos ML más sofisticados para inclusión financiera.",
                "severity": "high",
                "evidence": "Proyecto de regulación SBS 2025, presentado en noviembre 2025.",
            },
        ],
    },
    {
        "industry_target": "Servicios financieros",
        "profile_payload": {
            "industria": "Servicios financieros",
            "executive_summary": "Los holdings financieros peruanos (Credicorp, Intercorp) están buscando sinergias de datos entre sus subsidiarias para crear valor transversal. El desafío principal es la interoperabilidad entre bancos, seguros, AFPs y financieras dentro del mismo grupo. La oportunidad está en analytics unificado, gobierno de datos corporativo y experiencia cliente cross-subsidiaria.",
            "tendencias": [
                "Data mesh: arquitectura federada de datos por dominio de negocio",
                "Vista 360 del cliente: unificación cross-subsidiaria para up/cross-sell",
                "RegTech: automatización de compliance transversal al grupo",
                "ESG analytics: scorecards de sostenibilidad por portafolio",
                "Embedded finance: integración de servicios financieros en plataformas terceras",
            ],
            "benchmarks": {
                "cross_sell_ratio": "1.8 productos vs 3.2 benchmark global",
                "costo_compliance": "4-6% de ingresos vs 2-3% benchmark",
                "tiempo_lanzamiento_producto": "6-9 meses vs 3 meses benchmark",
            },
            "oportunidades": [
                "Vista 360 cliente: potencial de +S/.200M en cross-sell anual",
                "Gobierno de datos: reducción de 40% en costos de compliance",
                "Customer lifetime value analytics: mejora de 15-20% en retención",
            ],
        },
        "triggers_payload": [
            {
                "trigger_type": "budget_shift",
                "title": "Credicorp destina S/.200M a transformación digital 2025-2027",
                "rationale": "El holding más grande del Perú está priorizando sinergias tecnológicas entre BCP, Pacífico y Prima como palanca estratégica de crecimiento.",
                "severity": "high",
                "evidence": "Credicorp Annual Report 2025, investor presentation Q4.",
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# 3. HUMAN INSIGHTS — sales notes for top clients
# ---------------------------------------------------------------------------
HUMAN_INSIGHTS = [
    # BCP Insights
    {
        "company_id": "BCP",
        "author": "Miguel Ramirez",
        "department": "Operaciones",
        "sentiment": "Urgente",
        "raw_text": "Reunión con Diego Cavero (VP Ops): La conciliación bancaria manual les consume 4 horas diarias con un equipo de 12 personas. Errores de 3% en reconciliación interbancaria. Quieren RPA + ML para automatizar antes de la nueva regulación SBS de reportería en tiempo real. Presupuesto pre-aprobado para Q1 2026.",
        "structured_payload": [
            {"category": "pain_points", "value": "Conciliación manual de 4h diarias con 3% de errores y 12 personas dedicadas", "confidence": 0.95},
            {"category": "pain_points", "value": "Regulación SBS de reportería en tiempo real obliga a modernizar procesos", "confidence": 0.90},
            {"category": "decision_makers", "value": "Diego Cavero - VP de Operaciones y Tecnología", "confidence": 0.95},
            {"category": "sentiment", "value": "Presupuesto pre-aprobado, alta urgencia por nueva regulación", "confidence": 0.90},
        ],
        "source": "sales_meeting",
        "days_ago": 5,
    },
    {
        "company_id": "BCP",
        "author": "Ana Torres",
        "department": "TI",
        "sentiment": "Positivo",
        "raw_text": "Reunión con equipo de arquitectura de BCP para validar factibilidad técnica. Usan microservicios en Java Spring Boot + Oracle. Tienen ambiente de testing disponible. María Elena Vásquez (Dir. Transformación) dio luz verde para proof of concept de 6 semanas.",
        "structured_payload": [
            {"category": "pain_points", "value": "Infraestructura legacy Java Spring Boot + Oracle requiere integración cuidadosa", "confidence": 0.80},
            {"category": "decision_makers", "value": "María Elena Vásquez - Directora de Transformación Digital", "confidence": 0.95},
            {"category": "sentiment", "value": "Luz verde para PoC de 6 semanas, ambiente de testing disponible", "confidence": 0.92},
        ],
        "source": "sales_meeting",
        "days_ago": 3,
    },
    # INTERBANK Insights
    {
        "company_id": "INTERBANK",
        "author": "Carlos Mendoza",
        "department": "Operaciones",
        "sentiment": "Positivo",
        "raw_text": "Interbank quiere automatizar el backoffice de reclamos. Actualmente el 30% de reclamos excede el SLA de 15 días. Michela Casassa está muy interesada en una solución de clasificación automática + routing inteligente. Tienen datos de 500K reclamos históricos para entrenar modelos.",
        "structured_payload": [
            {"category": "pain_points", "value": "30% de reclamos fuera de SLA de 15 días por clasificación manual", "confidence": 0.92},
            {"category": "pain_points", "value": "Routing de reclamos a áreas incorrectas genera re-trabajo en 15% de casos", "confidence": 0.85},
            {"category": "decision_makers", "value": "Michela Casassa - VP Transformación Digital", "confidence": 0.95},
            {"category": "sentiment", "value": "Alta receptividad, 500K reclamos históricos disponibles para ML", "confidence": 0.90},
        ],
        "source": "sales_meeting",
        "days_ago": 8,
    },
    # ALICORP Insights
    {
        "company_id": "ALICORP",
        "author": "Roberto Silva",
        "department": "Operaciones",
        "sentiment": "Urgente",
        "raw_text": "Reunión con Paola Ruchman (VP Supply Chain): El forecast de demanda tiene 65% de precisión por SKU/tienda, muy debajo del benchmark de 90%. Esto genera S/.80M anuales en merma y sobrestock. Diego Torres (Dir. Innovación) quiere piloto con ML en 2 categorías top para Q1 2026. Presupuesto disponible de S/.500K para el piloto.",
        "structured_payload": [
            {"category": "pain_points", "value": "Forecast de demanda con 65% precisión genera S/.80M en pérdidas anuales", "confidence": 0.95},
            {"category": "pain_points", "value": "Merma en perecibles del 8% duplica el benchmark de la industria", "confidence": 0.90},
            {"category": "decision_makers", "value": "Paola Ruchman - VP de Supply Chain", "confidence": 0.95},
            {"category": "decision_makers", "value": "Diego Torres - Director de Innovación y Data", "confidence": 0.90},
            {"category": "sentiment", "value": "Presupuesto de S/.500K aprobado para piloto, urgencia alta", "confidence": 0.93},
        ],
        "source": "sales_meeting",
        "days_ago": 12,
    },
    # RIMAC Insights
    {
        "company_id": "RIMAC",
        "author": "Miguel Ramirez",
        "department": "Operaciones",
        "sentiment": "Urgente",
        "raw_text": "Rimac está perdiendo S/.50M anuales en fraude de siniestros. El procesamiento manual toma 30 días promedio. Carlos Valderrama quiere un PoC de automatización de siniestros simples (auto + salud menor) con IA para clasificación de documentos en Q2 2026.",
        "structured_payload": [
            {"category": "pain_points", "value": "Pérdida de S/.50M anuales por fraude en siniestros (8% vs 3% benchmark)", "confidence": 0.93},
            {"category": "pain_points", "value": "Procesamiento manual de siniestros toma 30 días promedio", "confidence": 0.90},
            {"category": "decision_makers", "value": "Carlos Valderrama - VP Operaciones", "confidence": 0.90},
            {"category": "sentiment", "value": "Urgen PoC para Q2 2026, siniestros simples como MVP", "confidence": 0.88},
        ],
        "source": "sales_meeting",
        "days_ago": 15,
    },
    # PLAZA VEA Insights
    {
        "company_id": "PLAZA VEA",
        "author": "Ana Torres",
        "department": "Comercial",
        "sentiment": "Urgente",
        "raw_text": "Plaza Vea está perdiendo 5-7% de ventas por problemas de disponibilidad en góndola. El pricing manual se revisa semanalmente pero competidores como Tottus ajustan diariamente. Roberto Seminario quiere explorar pricing dinámico con analytics y optimización de reposición automática.",
        "structured_payload": [
            {"category": "pain_points", "value": "5-7% de ventas perdidas por baja disponibilidad en góndola (88% vs 97% benchmark)", "confidence": 0.90},
            {"category": "pain_points", "value": "Pricing manual semanal vs competidores con pricing diario", "confidence": 0.88},
            {"category": "decision_makers", "value": "Roberto Seminario - VP de Operaciones", "confidence": 0.90},
            {"category": "sentiment", "value": "Presión competitiva alta, dispuestos a invertir si ROI claro", "confidence": 0.85},
        ],
        "source": "sales_meeting",
        "days_ago": 20,
    },
]


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def seed_profiles():
    count = 0
    for p in COMPANY_PROFILES:
        company_profile_repository.upsert_profile(
            company_id=p["company_id"],
            area=p["area"],
            profile_payload=p["profile_payload"],
        )
        count += 1
        print(f"  [profile] {p['company_id']} / {p['area']}")
    print(f"  => {count} profiles inserted/updated\n")


def seed_radiographies():
    count = 0
    for r in INDUSTRY_RADIOGRAPHIES:
        industry_radar_repository.upsert_radiography(
            industry_target=r["industry_target"],
            profile_payload=r["profile_payload"],
            triggers_payload=r["triggers_payload"],
        )
        count += 1
        print(f"  [radiography] {r['industry_target']}")
    print(f"  => {count} radiographies inserted/updated\n")


def seed_insights():
    count = 0
    for hi in HUMAN_INSIGHTS:
        structured = [StructuredInsightItem(**item) for item in hi["structured_payload"]]
        human_insight_repository.save(
            company_id=hi["company_id"],
            author=hi["author"],
            department=hi["department"],
            sentiment=hi["sentiment"],
            raw_text=hi["raw_text"],
            structured_payload=structured,
            source=hi["source"],
            parser_version="v1_seed",
        )
        count += 1
        print(f"  [insight] {hi['company_id']} by {hi['author']}")
    print(f"  => {count} insights inserted/updated\n")


def main():
    print("=" * 60)
    print("NEO Proposal Agent — Demo Data Seed")
    print("=" * 60)
    print()

    settings = get_settings()
    print(f"SQLite: {settings.sqlite_db_path}")
    print()

    print("[1/3] Seeding company profiles...")
    seed_profiles()

    print("[2/3] Seeding industry radiographies...")
    seed_radiographies()

    print("[3/3] Seeding human insights...")
    seed_insights()

    print("=" * 60)
    print("Seed complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
