from __future__ import annotations

import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import get_settings
from src.models.human_insight import ParsedHumanInsight, StructuredInsightItem
from src.services.errors import InsightParseError


def _extract_json_object(text: str) -> dict:
    body = text.strip()
    if body.startswith("```"):
        body = re.sub(r"^```(?:json)?", "", body).strip()
        body = re.sub(r"```$", "", body).strip()
    try:
        data = json.loads(body)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", body)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _normalize_department(value: str) -> str:
    cleaned = (value or "").strip().lower()
    mapping = {
        "ti": "TI",
        "it": "TI",
        "tecnologia": "TI",
        "tecnología": "TI",
        "finanzas": "Finanzas",
        "finance": "Finanzas",
        "marketing": "Marketing",
        "operaciones": "Operaciones",
        "ops": "Operaciones",
        "comercial": "Comercial",
        "ventas": "Comercial",
    }
    if cleaned in mapping:
        return mapping[cleaned]
    for key, mapped in mapping.items():
        if key in cleaned:
            return mapped
    return "General"


def _normalize_sentiment(value: str) -> str:
    cleaned = (value or "").strip().lower()
    mapping = {
        "riesgo": "Riesgo",
        "risk": "Riesgo",
        "urgente": "Urgente",
        "urgent": "Urgente",
        "positivo": "Positivo",
        "positive": "Positivo",
        "bloqueo": "Bloqueo",
        "blocked": "Bloqueo",
        "neutral": "Neutral",
    }
    if cleaned in mapping:
        return mapping[cleaned]
    for key, mapped in mapping.items():
        if key in cleaned:
            return mapped
    return "Neutral"


def _infer_department(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("cto", "sistemas", "infraestructura", "tecnolog", "arquitectura", "ciber")):
        return "TI"
    if any(token in lowered for token in ("cfo", "finanza", "presupuesto", "capex", "opex", "margen")):
        return "Finanzas"
    if any(token in lowered for token in ("marketing", "campaña", "campana", "leads", "conversion", "branding")):
        return "Marketing"
    if any(token in lowered for token in ("operacion", "logistica", "supply", "procesos", "backoffice")):
        return "Operaciones"
    if any(token in lowered for token in ("venta", "comercial", "pipeline", "deal", "cliente")):
        return "Comercial"
    return "General"


def _infer_sentiment(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("bloqueado", "bloqueo", "standstill", "detenido")):
        return "Bloqueo"
    if any(token in lowered for token in ("urgente", "hoy", "esta semana", "inmediato", "asap")):
        return "Urgente"
    if any(token in lowered for token in ("riesgo", "miedo", "temor", "no confia", "objecion", "objeción")):
        return "Riesgo"
    if any(token in lowered for token in ("interesado", "aprobado", "ok", "entusiasmado", "positivo")):
        return "Positivo"
    return "Neutral"


def _assert_required_categories(items: list[StructuredInsightItem]) -> None:
    required = {"pain_points", "decision_makers"}
    categories = {item.category for item in items}
    if not required.issubset(categories):
        missing = sorted(required - categories)
        raise InsightParseError(f"No se pudieron extraer categorias requeridas: {missing}")


def _normalize_payload(items: list[StructuredInsightItem]) -> list[StructuredInsightItem]:
    dedup: list[StructuredInsightItem] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item.category, item.value.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
    if len(dedup) > 18:
        dedup = dedup[:18]
    _assert_required_categories(dedup)
    return dedup


def _fallback_parsed_insight(text: str) -> ParsedHumanInsight:
    raw = text.strip()
    decision_hits: list[str] = []
    for candidate in ("gerente", "director", "cfo", "ceo", "cto", "jefe", "vp"):
        if candidate in raw.lower():
            decision_hits.append(candidate)
    decision_value = ", ".join(sorted(set(decision_hits))) if decision_hits else "No identificado"
    sentiment = _infer_sentiment(raw)
    payload = _normalize_payload(
        [
            StructuredInsightItem(category="pain_points", value=raw[:280], confidence=0.6),
            StructuredInsightItem(category="decision_makers", value=decision_value, confidence=0.5),
            StructuredInsightItem(category="sentiment", value=sentiment, confidence=0.6),
        ]
    )
    return ParsedHumanInsight(
        department=_infer_department(raw),
        sentiment=sentiment,
        structured_payload=payload,
    )


def parse_sales_insight_text(raw_text: str) -> ParsedHumanInsight:
    cleaned = " ".join(str(raw_text).replace("\x00", " ").split())
    if len(cleaned) < 10:
        raise InsightParseError("Texto insuficiente para extraer insight")
    if len(cleaned) > 1800:
        raise InsightParseError("Texto supera el limite permitido")

    settings = get_settings()
    if not settings.gemini_api_key:
        return _fallback_parsed_insight(cleaned)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.1,
        google_api_key=settings.gemini_api_key,
    )
    prompt = (
        "Eres un parser de inteligencia comercial B2B.\n"
        "Debes convertir texto libre en un objeto JSON estricto y valido con este schema exacto:\n"
        "{\"department\": \"TI|Finanzas|Marketing|Operaciones|Comercial|General\", "
        "\"sentiment\": \"Riesgo|Urgente|Positivo|Bloqueo|Neutral\", "
        "\"items\": [{\"category\": \"pain_points|decision_makers|sentiment\", \"value\": \"...\", \"confidence\": 0..1}]}\n"
        "Reglas:\n"
        "1) department debe deducirse del texto.\n"
        "2) sentiment debe representar el estado comercial actual.\n"
        "3) incluye al menos un pain_point y un decision_maker.\n"
        "4) responde SOLO JSON, sin texto adicional.\n\n"
        f"TEXTO:\n{cleaned}"
    )
    try:
        response = llm.invoke(prompt)
        data = _extract_json_object(str(response.content))
        if not data:
            raise InsightParseError("Gemini no devolvio un JSON valido")

        raw_items = data.get("items") or []
        items = _normalize_payload([StructuredInsightItem.model_validate(item) for item in raw_items])
        department = _normalize_department(str(data.get("department") or _infer_department(cleaned)))
        sentiment = _normalize_sentiment(str(data.get("sentiment") or _infer_sentiment(cleaned)))
        return ParsedHumanInsight(
            department=department,
            sentiment=sentiment,
            structured_payload=items,
        )
    except InsightParseError:
        raise
    except Exception:
        try:
            return _fallback_parsed_insight(cleaned)
        except Exception as exc:
            raise InsightParseError(f"No se pudo estructurar insight: {exc}") from exc
