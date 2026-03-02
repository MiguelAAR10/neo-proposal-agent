from __future__ import annotations

import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import get_settings
from src.models.human_insight import StructuredInsightItem
from src.services.errors import InsightParseError


def _extract_json_array(text: str) -> list[dict]:
    body = text.strip()
    if body.startswith("```"):
        body = re.sub(r"^```(?:json)?", "", body).strip()
        body = re.sub(r"```$", "", body).strip()
    try:
        data = json.loads(body)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", body)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _fallback_structured_payload(text: str) -> list[StructuredInsightItem]:
    raw = text.strip()
    lowered = raw.lower()

    sentiment = "neutral"
    if any(token in lowered for token in ("bloqueado", "molesto", "riesgo", "miedo", "caro", "no confia")):
        sentiment = "negative"
    elif any(token in lowered for token in ("interesado", "avance", "listo", "prioridad", "urgente")):
        sentiment = "positive"

    decision_hits: list[str] = []
    for candidate in ("gerente", "director", "cfo", "ceo", "cto", "jefe", "vp"):
        if candidate in lowered:
            decision_hits.append(candidate)
    decision_value = ", ".join(sorted(set(decision_hits))) if decision_hits else "No identificado"

    payload = [
        StructuredInsightItem(category="pain_points", value=raw[:280], confidence=0.6),
        StructuredInsightItem(category="decision_makers", value=decision_value, confidence=0.5),
        StructuredInsightItem(category="sentiment", value=sentiment, confidence=0.5),
    ]
    _assert_required_categories(payload)
    return payload


def _assert_required_categories(items: list[StructuredInsightItem]) -> None:
    required = {"pain_points", "decision_makers", "sentiment"}
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


def parse_sales_insight_text(raw_text: str) -> list[StructuredInsightItem]:
    cleaned = " ".join(str(raw_text).replace("\x00", " ").split())
    if len(cleaned) < 10:
        raise InsightParseError("Texto insuficiente para extraer insight")
    if len(cleaned) > 1800:
        raise InsightParseError("Texto supera el limite permitido")

    settings = get_settings()
    if not settings.gemini_api_key:
        return _normalize_payload(_fallback_structured_payload(cleaned))

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.1,
        google_api_key=settings.gemini_api_key,
    )
    prompt = (
        "Eres un parser de inteligencia comercial.\n"
        "Convierte el texto libre en un JSON array estricto.\n"
        "Cada item debe tener schema: {\"category\": \"pain_points|decision_makers|sentiment\", \"value\": \"...\", \"confidence\": 0..1}.\n"
        "No incluyas texto fuera del JSON.\n"
        "Asegura al menos 1 item por categoria obligatoria.\n\n"
        f"TEXTO:\n{cleaned}"
    )
    try:
        response = llm.invoke(prompt)
        payload = _extract_json_array(str(response.content))
        parsed = _normalize_payload([StructuredInsightItem.model_validate(item) for item in payload])
        return parsed
    except InsightParseError:
        raise
    except Exception:
        try:
            return _normalize_payload(_fallback_structured_payload(cleaned))
        except Exception as exc:
            raise InsightParseError(f"No se pudo estructurar insight: {exc}") from exc
