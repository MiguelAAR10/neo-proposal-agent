from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Header, Response

from src.api.deps import (
    chat_audit_store,
    intel_metrics,
    require_admin_access,
    search_metrics,
    session_funnel_store,
    settings,
)
from src.services.chat_alerts import ChatAlertThresholds, build_chat_alerts

router = APIRouter(tags=["ops"])


def _build_thresholds() -> ChatAlertThresholds:
    return ChatAlertThresholds(
        min_events=settings.chat_alert_min_events,
        block_rate_warning=settings.chat_alert_block_rate_warning,
        block_rate_critical=settings.chat_alert_block_rate_critical,
        no_case_usage_warning=settings.chat_alert_no_case_usage_warning,
        company_concentration_warning=settings.chat_alert_company_concentration_warning,
    )


def _resolve_updated_after(time_range: str) -> str | None:
    now_utc = datetime.now(timezone.utc)
    if time_range == "1h":
        return (now_utc - timedelta(hours=1)).isoformat()
    if time_range == "24h":
        return (now_utc - timedelta(hours=24)).isoformat()
    if time_range == "7d":
        return (now_utc - timedelta(days=7)).isoformat()
    return None


@router.get("/ops/metrics")
async def get_ops_metrics(authorization: str | None = Header(default=None)):
    """Métricas operativas livianas para seguimiento de SLA de búsqueda."""
    require_admin_access(authorization)
    return {
        "status": "ok",
        "environment": settings.app_env,
        "search": search_metrics.snapshot(),
        "intel": intel_metrics.snapshot(),
    }


@router.get("/ops/chat-audit")
async def get_chat_audit(
    authorization: str | None = Header(default=None),
    limit: int = 100,
    status: str | None = None,
):
    """Traza operativa de chat/guardrails para auditoria."""
    require_admin_access(authorization)
    return {
        "status": "ok",
        "environment": settings.app_env,
        "chat_audit": chat_audit_store.snapshot(limit=limit, status=status),
    }


@router.get("/ops/chat-audit/export")
async def export_chat_audit(
    authorization: str | None = Header(default=None),
    format: Literal["json", "csv"] = "json",
    limit: int = 200,
    status: str | None = None,
):
    """Exporta trazas operativas de chat en JSON/CSV."""
    require_admin_access(authorization)
    snap = chat_audit_store.snapshot(limit=limit, status=status)

    if format == "json":
        return {
            "status": "ok",
            "environment": settings.app_env,
            "chat_audit_export": snap,
        }

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "ts_utc", "thread_id", "status", "guardrail_code",
            "used_case_count", "used_case_ids", "message_preview",
        ],
    )
    writer.writeheader()
    for row in snap.get("items", []):
        writer.writerow({
            "ts_utc": row.get("ts_utc", ""),
            "thread_id": row.get("thread_id", ""),
            "status": row.get("status", ""),
            "guardrail_code": row.get("guardrail_code", ""),
            "used_case_count": row.get("used_case_count", 0),
            "used_case_ids": ",".join(str(v) for v in row.get("used_case_ids", [])),
            "message_preview": row.get("message_preview", ""),
        })

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="chat_audit_export.csv"'},
    )


@router.get("/ops/chat-analytics")
async def get_chat_analytics(
    authorization: str | None = Header(default=None),
    status: str | None = None,
):
    """KPIs operativos de chat contextual y guardrails."""
    require_admin_access(authorization)
    return {
        "status": "ok",
        "environment": settings.app_env,
        "chat_analytics": chat_audit_store.analytics(status=status),
    }


@router.get("/ops/chat-alerts")
async def get_chat_alerts(
    authorization: str | None = Header(default=None),
    status: str | None = None,
):
    """Alertas operativas automáticas sobre analítica de chat."""
    require_admin_access(authorization)
    analytics = chat_audit_store.analytics(status=status)
    thresholds = _build_thresholds()
    alerts = build_chat_alerts(analytics, thresholds)
    return {
        "status": "ok",
        "environment": settings.app_env,
        "thresholds": {
            "min_events": thresholds.min_events,
            "block_rate_warning": thresholds.block_rate_warning,
            "block_rate_critical": thresholds.block_rate_critical,
            "no_case_usage_warning": thresholds.no_case_usage_warning,
            "company_concentration_warning": thresholds.company_concentration_warning,
        },
        "chat_analytics": analytics,
        "chat_alerts": alerts,
    }


@router.get("/ops/chat-alerts/history")
async def get_chat_alerts_history(
    authorization: str | None = Header(default=None),
    bucket: Literal["hour", "day"] = "hour",
    limit_buckets: int = 48,
    status: str | None = None,
):
    """Historial temporal de alertas de chat para analisis de tendencia."""
    require_admin_access(authorization)
    thresholds = _build_thresholds()
    history = chat_audit_store.analytics_history(
        bucket=bucket, limit_buckets=limit_buckets, status=status,
    )
    enriched_series: list[dict] = []
    for item in history.get("series", []):
        metrics = item.get("metrics", {})
        enriched_series.append({
            "bucket_start_utc": item.get("bucket_start_utc"),
            "metrics": metrics,
            "alerts": build_chat_alerts(metrics, thresholds),
        })

    return {
        "status": "ok",
        "environment": settings.app_env,
        "bucket": bucket,
        "thresholds": {
            "min_events": thresholds.min_events,
            "block_rate_warning": thresholds.block_rate_warning,
            "block_rate_critical": thresholds.block_rate_critical,
            "no_case_usage_warning": thresholds.no_case_usage_warning,
            "company_concentration_warning": thresholds.company_concentration_warning,
        },
        "history": {
            "source": history.get("source"),
            "returned_buckets": len(enriched_series),
            "series": enriched_series,
        },
    }


@router.get("/ops/funnel")
async def get_ops_funnel(
    authorization: str | None = Header(default=None),
    company: str | None = None,
    time_range: Literal["1h", "24h", "7d", "all"] = "24h",
    completed_only: bool = False,
    sort_by: str = "last_update_utc",
    sort_dir: Literal["asc", "desc"] = "desc",
    page: int = 1,
    page_size: int = 25,
):
    """Conversión operativa del flujo MVP por sesiones (thread)."""
    require_admin_access(authorization)
    safe_page = max(1, int(page))
    safe_page_size = max(1, min(int(page_size), 200))
    offset = (safe_page - 1) * safe_page_size
    updated_after_utc = _resolve_updated_after(time_range)

    funnel_summary = session_funnel_store.summary(
        company=company, updated_after_utc=updated_after_utc,
        completed_only=completed_only, sort_by=sort_by, sort_dir=sort_dir,
    )
    sessions = session_funnel_store.snapshot(
        limit=safe_page_size, offset=offset, company=company,
        updated_after_utc=updated_after_utc, completed_only=completed_only,
        sort_by=sort_by, sort_dir=sort_dir,
    )
    return {
        "status": "ok",
        "environment": settings.app_env,
        "query": {
            "company": company, "time_range": time_range,
            "completed_only": completed_only, "sort_by": sort_by,
            "sort_dir": sort_dir, "page": safe_page,
            "page_size": safe_page_size, "offset": offset,
        },
        "funnel": funnel_summary,
        "sessions": sessions,
    }


@router.get("/ops/funnel/export")
async def export_ops_funnel(
    authorization: str | None = Header(default=None),
    format: Literal["json", "csv"] = "csv",
    company: str | None = None,
    time_range: Literal["1h", "24h", "7d", "all"] = "24h",
    completed_only: bool = False,
    sort_by: str = "last_update_utc",
    sort_dir: Literal["asc", "desc"] = "desc",
):
    """Exporta sesiones de funnel con filtros server-side."""
    require_admin_access(authorization)
    updated_after_utc = _resolve_updated_after(time_range)

    snap = session_funnel_store.snapshot(
        limit=5000, offset=0, company=company,
        updated_after_utc=updated_after_utc, completed_only=completed_only,
        sort_by=sort_by, sort_dir=sort_dir,
    )
    if format == "json":
        return {
            "status": "ok",
            "environment": settings.app_env,
            "query": {
                "company": company, "time_range": time_range,
                "completed_only": completed_only, "sort_by": sort_by, "sort_dir": sort_dir,
            },
            "sessions": snap,
        }

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "thread_id", "empresa", "area", "total_cases", "selected_count",
            "proposal_generated", "refined_count", "chat_count",
            "guardrail_blocked_count", "started_at_utc", "last_update_utc",
        ],
    )
    writer.writeheader()
    for row in snap.get("items", []):
        writer.writerow({
            "thread_id": row.get("thread_id", ""),
            "empresa": row.get("empresa", ""),
            "area": row.get("area", ""),
            "total_cases": row.get("total_cases", 0),
            "selected_count": row.get("selected_count", 0),
            "proposal_generated": row.get("proposal_generated", False),
            "refined_count": row.get("refined_count", 0),
            "chat_count": row.get("chat_count", 0),
            "guardrail_blocked_count": row.get("guardrail_blocked_count", 0),
            "started_at_utc": row.get("started_at_utc", ""),
            "last_update_utc": row.get("last_update_utc", ""),
        })

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="ops_funnel_export.csv"'},
    )


@router.get("/ops/funnel/history")
async def get_ops_funnel_history(
    authorization: str | None = Header(default=None),
    bucket: Literal["hour", "day"] = "hour",
    limit_buckets: int = 48,
    company: str | None = None,
    time_range: Literal["1h", "24h", "7d", "all"] = "24h",
    completed_only: bool = False,
):
    """Historial temporal del funnel para detectar tendencia de conversión."""
    require_admin_access(authorization)
    updated_after_utc = _resolve_updated_after(time_range)

    history = session_funnel_store.history(
        bucket=bucket, limit_buckets=limit_buckets,
        company=company, updated_after_utc=updated_after_utc,
        completed_only=completed_only,
    )
    return {
        "status": "ok",
        "environment": settings.app_env,
        "query": {
            "bucket": bucket,
            "limit_buckets": max(1, min(int(limit_buckets), 720)),
            "company": company, "time_range": time_range,
            "completed_only": completed_only,
        },
        "history": history,
    }
