from __future__ import annotations

import unicodedata
from typing import Any

_PRIORITIZED_CLIENTS: tuple[str, ...] = (
    "BCP",
    "INTERBANK",
    "BBVA",
    "ALICORP",
    "RIMAC",
    "PACIFICO",
    "SCOTIABANK",
    "MIBANCO",
    "CREDICORP",
    "PLAZA VEA",
    "FALABELLA",
    "SODIMAC",
)

_PRIORITIZED_CLIENT_CONTEXT: dict[str, dict[str, Any]] = {
    "BCP": {
        "vertical": "Banca",
        "priorities": ["eficiencia operativa", "riesgo y cumplimiento", "experiencia digital"],
        "constraints": ["gobierno de datos", "trazabilidad regulatoria"],
    },
    "INTERBANK": {
        "vertical": "Banca",
        "priorities": ["omnicanalidad", "productividad comercial", "automatizacion de backoffice"],
        "constraints": ["integracion con core bancario", "seguridad de datos"],
    },
    "BBVA": {
        "vertical": "Banca",
        "priorities": ["analitica de riesgo", "eficiencia de procesos", "escalabilidad digital"],
        "constraints": ["cumplimiento", "adopcion operacional"],
    },
    "ALICORP": {
        "vertical": "Consumo masivo",
        "priorities": ["cadena de suministro", "forecast de demanda", "rentabilidad por canal"],
        "constraints": ["calidad de datos comerciales", "tiempo de respuesta"],
    },
    "RIMAC": {
        "vertical": "Seguros",
        "priorities": ["siniestralidad", "automatizacion de atencion", "deteccion de fraude"],
        "constraints": ["cumplimiento", "explicabilidad de modelos"],
    },
    "PACIFICO": {
        "vertical": "Seguros",
        "priorities": ["retencion de cartera", "tiempo de resolucion", "eficiencia de operaciones"],
        "constraints": ["integridad documental", "servicio al cliente"],
    },
    "SCOTIABANK": {
        "vertical": "Banca",
        "priorities": ["scoring y originacion", "productividad de operaciones", "cross-sell"],
        "constraints": ["riesgo operativo", "observabilidad de procesos"],
    },
    "MIBANCO": {
        "vertical": "Microfinanzas",
        "priorities": ["evaluacion crediticia", "productividad de asesores", "gestion de cartera"],
        "constraints": ["calidad de data de campo", "capilaridad operacional"],
    },
    "CREDICORP": {
        "vertical": "Servicios financieros",
        "priorities": ["sinergias entre unidades", "analitica de valor", "eficiencia transversal"],
        "constraints": ["interoperabilidad", "gobierno corporativo de datos"],
    },
    "PLAZA VEA": {
        "vertical": "Retail",
        "priorities": ["abastecimiento", "pricing inteligente", "experiencia omnicanal"],
        "constraints": ["margen comercial", "disponibilidad en tienda"],
    },
    "FALABELLA": {
        "vertical": "Retail",
        "priorities": ["eficiencia logistico-comercial", "fidelizacion", "optimizacion de surtido"],
        "constraints": ["coordinacion cross-canal", "time-to-value corto"],
    },
    "SODIMAC": {
        "vertical": "Retail",
        "priorities": ["planeamiento de inventario", "servicio postventa", "productividad de tienda"],
        "constraints": ["integracion omnicanal", "calidad de ejecucion"],
    },
}


def normalize_company_name(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    normalized = unicodedata.normalize("NFKD", raw)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_only.upper().split())


def get_prioritized_clients() -> list[str]:
    return list(_PRIORITIZED_CLIENTS)


def is_prioritized_client(company_name: str) -> bool:
    return normalize_company_name(company_name) in _PRIORITIZED_CLIENTS


def get_prioritized_client_context(company_name: str) -> dict[str, Any]:
    normalized = normalize_company_name(company_name)
    base = _PRIORITIZED_CLIENT_CONTEXT.get(normalized)
    if not base:
        return {}
    return {
        "client_name": normalized,
        "vertical": base.get("vertical"),
        "priorities": list(base.get("priorities", [])),
        "constraints": list(base.get("constraints", [])),
        "source": "prioritized_clients_v1",
    }
