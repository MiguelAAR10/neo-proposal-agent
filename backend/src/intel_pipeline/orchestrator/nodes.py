from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import Settings, get_settings
from src.intel_pipeline.collectors.agentic_tools import (
    get_financial_ticker,
    scrape_regulatory_site,
    search_market_trends,
)
from src.intel_pipeline.orchestrator.state import RadarState
from src.models.industry_radar import IndustryRadiography, IndustryTrigger, RadarSignal
from src.services.intel_storage import industry_radar_repository


def _extract_json_object(text: str) -> dict[str, Any]:
    body = text.strip()
    if body.startswith("```"):
        body = re.sub(r"^```(?:json)?", "", body).strip()
        body = re.sub(r"```$", "", body).strip()
    try:
        parsed = json.loads(body)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", body)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _default_ticker_for_industry(industry_target: str) -> str:
    low = industry_target.strip().lower()
    if "banca" in low or "finanz" in low:
        return "BAP"
    if "retail" in low:
        return "WMT"
    if "telecom" in low or "telco" in low:
        return "AMX"
    return "SPY"


def _fallback_tool_plan(industry_target: str) -> tuple[list[str], str]:
    tools = ["search_market_trends"]
    ticker = _default_ticker_for_industry(industry_target)
    low = industry_target.strip().lower()
    if "banca" in low or "finanz" in low or "seguros" in low:
        tools.append("scrape_regulatory_site")
    tools.append("get_financial_ticker")
    return tools, ticker


def _decide_tool_plan_with_llm(industry_target: str, settings: Settings) -> tuple[list[str], str]:
    if not settings.gemini_api_key:
        return _fallback_tool_plan(industry_target)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.0,
        google_api_key=settings.gemini_api_key,
    )
    prompt = (
        "Eres planner de un radar de inteligencia macro.\n"
        "Devuelve SOLO JSON con schema: "
        "{\"tools\":[\"search_market_trends|scrape_regulatory_site|get_financial_ticker\"],\"ticker\":\"...\"}\n"
        "Reglas:\n"
        "1) Incluye search_market_trends siempre.\n"
        "2) Si la industria es regulada (banca, seguros, finanzas), incluye scrape_regulatory_site.\n"
        "3) Incluye get_financial_ticker para señales de mercado.\n"
        f"Industria objetivo: {industry_target}"
    )
    try:
        response = llm.invoke(prompt)
        data = _extract_json_object(str(response.content))
        tools_raw = data.get("tools") if isinstance(data.get("tools"), list) else []
        allowed = {"search_market_trends", "scrape_regulatory_site", "get_financial_ticker"}
        tools = [tool for tool in [str(item) for item in tools_raw] if tool in allowed]
        if "search_market_trends" not in tools:
            tools.insert(0, "search_market_trends")
        if "get_financial_ticker" not in tools:
            tools.append("get_financial_ticker")
        ticker = str(data.get("ticker") or _default_ticker_for_industry(industry_target)).upper()
        return tools[:3], ticker
    except Exception:
        return _fallback_tool_plan(industry_target)


def collect_signals_node(state: RadarState) -> RadarState:
    if state.get("error"):
        return state

    industry_target = " ".join(str(state.get("industry_target") or "").split())
    if not industry_target:
        state["error"] = "industry_target es requerido"
        return state

    settings = get_settings()
    force_mock = bool(state.get("force_mock_tools", False))
    if force_mock:
        tools, ticker = _fallback_tool_plan(industry_target)
    else:
        tools, ticker = _decide_tool_plan_with_llm(industry_target, settings)

    signals: list[RadarSignal] = []
    for tool in tools:
        try:
            if tool == "search_market_trends":
                signals.extend(search_market_trends(industry_target, force_mock_tools=force_mock))
            elif tool == "scrape_regulatory_site":
                signals.extend(scrape_regulatory_site(industry_target, force_mock_tools=force_mock))
            elif tool == "get_financial_ticker":
                signals.extend(get_financial_ticker(ticker, force_mock_tools=force_mock))
        except Exception as exc:
            signals.append(
                RadarSignal(
                    source="tool_error",
                    signal_type="market_trend",
                    content=f"Tool {tool} fallo: {exc}",
                    confidence=0.2,
                    captured_at=datetime.now(timezone.utc).isoformat(),
                )
            )

    state["signals_structured"] = [signal.model_dump() for signal in signals]
    state["raw_signals"] = [f"[{signal.source}] {signal.content}" for signal in signals]
    state.setdefault("critical_triggers_found", [])
    state.setdefault("industry_radiography", {})
    return state


def _fallback_evaluate_triggers(raw_signals: list[str]) -> list[IndustryTrigger]:
    triggers: list[IndustryTrigger] = []
    for signal in raw_signals:
        text = signal.strip()
        low = text.lower()
        if "resoluci" in low or "circular" in low or "regulator" in low or "sbs" in low or "elperuano" in low:
            triggers.append(
                IndustryTrigger(
                    trigger_type="new_law",
                    title="Cambio regulatorio detectado",
                    rationale="Se detectó referencia normativa o regulatoria reciente.",
                    severity="high",
                    evidence=text[:450],
                )
            )

        pct_match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", text)
        if pct_match:
            try:
                pct_value = float(pct_match.group(1))
                if pct_value <= -5.0:
                    triggers.append(
                        IndustryTrigger(
                            trigger_type="stock_drop",
                            title="Caída relevante en ticker de referencia",
                            rationale="La variación diaria supera el umbral de -5%.",
                            severity="high",
                            evidence=text[:450],
                        )
                    )
            except ValueError:
                pass

        if "gartner" in low or "mckinsey" in low or "bcg" in low or "forrester" in low:
            triggers.append(
                IndustryTrigger(
                    trigger_type="analyst_alert",
                    title="Reporte de consultora top detectado",
                    rationale="Se identificó señal de consultora estratégica con impacto potencial.",
                    severity="medium",
                    evidence=text[:450],
                )
            )

    if not triggers and raw_signals:
        triggers.append(
            IndustryTrigger(
                trigger_type="other",
                title="Señal macro en observación",
                rationale="No hubo trigger crítico explícito; mantener monitoreo continuo.",
                severity="low",
                evidence=raw_signals[0][:450],
            )
        )
    return triggers[:8]


def _evaluate_triggers_with_llm(
    *,
    industry_target: str,
    raw_signals: list[str],
    settings: Settings,
) -> list[IndustryTrigger]:
    if not settings.gemini_api_key:
        return _fallback_evaluate_triggers(raw_signals)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.0,
        google_api_key=settings.gemini_api_key,
    )
    joined = "\n".join(f"- {item}" for item in raw_signals[:12])
    prompt = (
        "Analiza señales macro y devuelve SOLO triggers críticos en JSON.\n"
        "Schema exacto: {\"triggers\":[{\"trigger_type\":\"new_law|stock_drop|analyst_alert|budget_shift|other\","
        "\"title\":\"...\",\"rationale\":\"...\",\"severity\":\"high|medium|low\",\"evidence\":\"...\"}]}\n"
        "Reglas estrictas:\n"
        "1) Solo incluir triggers si hay evidencia textual concreta.\n"
        "2) Detecta `new_law` para nuevas leyes/resoluciones/circulares regulatorias.\n"
        "3) Detecta `stock_drop` solo si variación <= -5%.\n"
        "4) Detecta `analyst_alert` para reportes de Gartner/McKinsey/BCG/Forrester.\n"
        "5) Responde JSON válido, sin explicación.\n"
        f"Industria: {industry_target}\n"
        f"Señales:\n{joined}"
    )
    try:
        response = llm.invoke(prompt)
        data = _extract_json_object(str(response.content))
        rows = data.get("triggers") if isinstance(data.get("triggers"), list) else []
        parsed = [IndustryTrigger.model_validate(row) for row in rows]
        if parsed:
            return parsed[:8]
        return _fallback_evaluate_triggers(raw_signals)
    except Exception:
        return _fallback_evaluate_triggers(raw_signals)


def evaluate_triggers_node(state: RadarState) -> RadarState:
    if state.get("error"):
        return state

    raw_signals = list(state.get("raw_signals") or [])
    if not raw_signals:
        state["error"] = "No hay señales para evaluar"
        return state

    settings = get_settings()
    industry_target = str(state.get("industry_target") or "General")
    force_mock = bool(state.get("force_mock_tools", False))
    if force_mock:
        triggers = _fallback_evaluate_triggers(raw_signals)
    else:
        triggers = _evaluate_triggers_with_llm(
            industry_target=industry_target,
            raw_signals=raw_signals,
            settings=settings,
        )
    state["trigger_objects"] = [trigger.model_dump() for trigger in triggers]
    state["critical_triggers_found"] = [f"{item.trigger_type}: {item.title}" for item in triggers]
    return state


def _build_recommendations(triggers: list[IndustryTrigger]) -> list[str]:
    recommendations: list[str] = []
    high_count = sum(1 for item in triggers if item.severity == "high")
    if high_count:
        recommendations.append("Activar war-room comercial con foco en riesgos críticos de corto plazo.")
    if any(item.trigger_type == "new_law" for item in triggers):
        recommendations.append("Recalibrar narrativa comercial con foco en cumplimiento y trazabilidad.")
    if any(item.trigger_type == "stock_drop" for item in triggers):
        recommendations.append("Priorizar casos de eficiencia operativa y reducción de costos.")
    if not recommendations:
        recommendations.append("Mantener monitoreo semanal y validar impacto con equipo de ventas.")
    return recommendations[:4]


def update_industry_profile_node(state: RadarState) -> RadarState:
    if state.get("error"):
        return state

    industry_target = str(state.get("industry_target") or "").strip()
    if not industry_target:
        state["error"] = "industry_target vacío"
        return state

    trigger_rows = state.get("trigger_objects") or []
    triggers = [IndustryTrigger.model_validate(row) for row in trigger_rows]
    sources_checked = sorted(
        {
            str(item.get("source") or "unknown")
            for item in (state.get("signals_structured") or [])
            if isinstance(item, dict)
        }
    )

    if triggers:
        summary = (
            f"Radar para {industry_target}: se detectaron {len(triggers)} triggers, "
            f"incluyendo eventos de severidad alta que requieren acción comercial."
        )
    else:
        summary = f"Radar para {industry_target}: sin triggers críticos; mantener monitoreo activo."

    profile = IndustryRadiography(
        industry_target=industry_target,
        executive_summary=summary,
        critical_triggers=triggers,
        recommendations=_build_recommendations(triggers),
        sources_checked=sources_checked,
    )

    stored = industry_radar_repository.upsert_radiography(
        industry_target=industry_target,
        profile_payload=profile.model_dump(),
        triggers_payload=[item.model_dump() for item in triggers],
    )

    payload = dict(stored.profile_payload or {})
    payload["updated_at"] = stored.updated_at
    state["industry_radiography"] = payload
    return state
