from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatAlertThresholds:
    min_events: int
    block_rate_warning: float
    block_rate_critical: float
    no_case_usage_warning: float
    company_concentration_warning: float


def _playbook_for_code(code: str) -> dict[str, str]:
    if code == "HIGH_GUARDRAIL_BLOCK_RATE":
        return {
            "priority": "p0",
            "owner": "backend-oncall",
            "playbook_hint": "Revisar top_guardrail_codes y prompts de entrada; ajustar guardrails/prompt de sistema y validar en sandbox.",
        }
    if code == "ELEVATED_GUARDRAIL_BLOCK_RATE":
        return {
            "priority": "p1",
            "owner": "backend",
            "playbook_hint": "Auditar muestras recientes bloqueadas y clasificar falsos positivos antes de ajustar umbrales.",
        }
    if code == "LOW_CASE_GROUNDING":
        return {
            "priority": "p1",
            "owner": "product-backend",
            "playbook_hint": "Revisar selección de casos y calidad de evidencia URL/KPI; reforzar prompt para citar casos seleccionados.",
        }
    if code == "HIGH_COMPANY_CONCENTRATION":
        return {
            "priority": "p2",
            "owner": "ops-product",
            "playbook_hint": "Verificar sesgo de adopción por cuenta y balancear enablement en otras empresas priorizadas.",
        }
    if code == "LOW_SAMPLE_SIZE":
        return {
            "priority": "p3",
            "owner": "ops",
            "playbook_hint": "Esperar más eventos antes de decisiones estructurales; mantener monitoreo.",
        }
    return {
        "priority": "p3",
        "owner": "ops",
        "playbook_hint": "Revisar manualmente la señal y confirmar impacto.",
    }


def build_chat_alerts(analytics: dict[str, Any], thresholds: ChatAlertThresholds) -> dict[str, Any]:
    events = int(analytics.get("window_events", 0) or 0)
    block_rate = float(analytics.get("guardrail_block_rate", 0.0) or 0.0)
    no_case_usage_rate = float(analytics.get("no_case_usage_rate", 0.0) or 0.0)
    top_company_share = float(analytics.get("top_company_share", 0.0) or 0.0)

    alerts: list[dict[str, Any]] = []
    if events < thresholds.min_events:
        alerts.append(
            {
                "severity": "info",
                "code": "LOW_SAMPLE_SIZE",
                "message": f"Muestra insuficiente para alertas fuertes ({events}/{thresholds.min_events}).",
                "value": events,
                "threshold": thresholds.min_events,
                **_playbook_for_code("LOW_SAMPLE_SIZE"),
            }
        )
        return {
            "severity": "info",
            "alerts": alerts,
            "window_events": events,
            "ready_for_strict_alerting": False,
            "recommended_actions": [alerts[0]["playbook_hint"]],
        }

    if block_rate >= thresholds.block_rate_critical:
        alerts.append(
            {
                "severity": "critical",
                "code": "HIGH_GUARDRAIL_BLOCK_RATE",
                "message": "La tasa de bloqueos por guardrails supera el umbral critico.",
                "value": round(block_rate, 4),
                "threshold": thresholds.block_rate_critical,
                **_playbook_for_code("HIGH_GUARDRAIL_BLOCK_RATE"),
            }
        )
    elif block_rate >= thresholds.block_rate_warning:
        alerts.append(
            {
                "severity": "warning",
                "code": "ELEVATED_GUARDRAIL_BLOCK_RATE",
                "message": "La tasa de bloqueos por guardrails supera el umbral de alerta.",
                "value": round(block_rate, 4),
                "threshold": thresholds.block_rate_warning,
                **_playbook_for_code("ELEVATED_GUARDRAIL_BLOCK_RATE"),
            }
        )

    if no_case_usage_rate >= thresholds.no_case_usage_warning:
        alerts.append(
            {
                "severity": "warning",
                "code": "LOW_CASE_GROUNDING",
                "message": "Las respuestas OK muestran baja ancla en casos (used_case_count=0).",
                "value": round(no_case_usage_rate, 4),
                "threshold": thresholds.no_case_usage_warning,
                **_playbook_for_code("LOW_CASE_GROUNDING"),
            }
        )

    if top_company_share >= thresholds.company_concentration_warning:
        alerts.append(
            {
                "severity": "warning",
                "code": "HIGH_COMPANY_CONCENTRATION",
                "message": "La actividad de chat esta concentrada en una sola empresa.",
                "value": round(top_company_share, 4),
                "threshold": thresholds.company_concentration_warning,
                **_playbook_for_code("HIGH_COMPANY_CONCENTRATION"),
            }
        )

    if any(alert["severity"] == "critical" for alert in alerts):
        severity = "critical"
    elif any(alert["severity"] == "warning" for alert in alerts):
        severity = "warning"
    else:
        severity = "ok"

    recommended_actions: list[str] = []
    seen = set()
    for alert in alerts:
        hint = str(alert.get("playbook_hint") or "").strip()
        if hint and hint not in seen:
            recommended_actions.append(hint)
            seen.add(hint)

    return {
        "severity": severity,
        "alerts": alerts,
        "window_events": events,
        "ready_for_strict_alerting": True,
        "recommended_actions": recommended_actions,
    }
