from __future__ import annotations

import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import get_settings
from src.models.human_insight import StructuredInsightItem


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

    return [
        StructuredInsightItem(category="pain_points", value=raw[:500], confidence=0.6),
        StructuredInsightItem(category="decision_makers", value=decision_value, confidence=0.5),
        StructuredInsightItem(category="sentiment", value=sentiment, confidence=0.5),
    ]


def parse_sales_insight_text(raw_text: str) -> list[StructuredInsightItem]:
    settings = get_settings()
    if not settings.gemini_api_key:
        return _fallback_structured_payload(raw_text)

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
        f"TEXTO:\n{raw_text}"
    )
    try:
        response = llm.invoke(prompt)
        payload = _extract_json_array(str(response.content))
        parsed = [StructuredInsightItem.model_validate(item) for item in payload]
        categories = {item.category for item in parsed}
        required = {"pain_points", "decision_makers", "sentiment"}
        if not required.issubset(categories):
            return _fallback_structured_payload(raw_text)
        return parsed
    except Exception:
        return _fallback_structured_payload(raw_text)
