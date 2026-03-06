"""Shared dependencies for API routers.

Replaces the circular _main() import pattern with direct imports.
All helpers that routers need are exposed here.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import HTTPException

from src.agent.graph import graph
from src.api.schemas import AgentStateResponse
from src.config import get_settings
from src.services.chat_audit import chat_audit_store
from src.services.chat_guardrails import evaluate_chat_message
from src.services.errors import BackendDomainError, ExternalDependencyTimeout
from src.services.intel_metrics import intel_metrics
from src.services.llm_pool import get_chat_llm
from src.services.metrics import search_metrics
from src.services.prioritized_clients import (
    get_prioritized_client_context,
    get_prioritized_clients,
    get_prioritized_clients_catalog,
    is_prioritized_client,
    normalize_company_name,
)
from src.services.proposal_context import (
    filter_selected_cases,
    format_cases_for_prompt,
    validate_selected_cases_have_url,
)
from src.services.rate_limit import rate_limiter
from src.services.search_service import search_cases_with_sla
from src.services.session_funnel import session_funnel_store
from src.tools.qdrant_tool import db_connection

logger = logging.getLogger("neo_api_v2")
settings = get_settings()

_INTERNAL_SERVER_ERROR_DETAIL = {"error": "Internal Server Error", "code": 500}
_LLM_TIMEOUT_SEC = 20.0


def raise_domain_http(error: BackendDomainError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )


def raise_internal_server_error(message: str) -> None:
    logger.exception(message)
    raise HTTPException(status_code=500, detail=_INTERNAL_SERVER_ERROR_DETAIL)


def require_admin_access(authorization: str | None) -> None:
    if settings.is_non_local_env and not settings.admin_token:
        raise HTTPException(
            status_code=500,
            detail={"code": "MISCONFIGURATION", "message": "ADMIN_TOKEN obligatorio en staging/prod."},
        )
    if settings.admin_token:
        expected = f"Bearer {settings.admin_token}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Unauthorized"})


def map_state_response(
    thread_id: str,
    state_values: dict,
    status: Optional[str] = None,
) -> AgentStateResponse:
    resolved_status = status
    if resolved_status is None:
        resolved_status = "completed" if state_values.get("propuesta_final") else "awaiting_selection"

    return AgentStateResponse(
        thread_id=thread_id,
        empresa=state_values.get("empresa", ""),
        area=state_values.get("area", ""),
        problema=state_values.get("problema", ""),
        casos_encontrados=state_values.get("casos_encontrados", []),
        neo_cases=state_values.get("neo_cases", []),
        ai_cases=state_values.get("ai_cases", []),
        top_match_global=state_values.get("top_match_global"),
        top_match_global_reason=state_values.get("top_match_global_reason"),
        casos_seleccionados_ids=state_values.get("casos_seleccionados_ids", []),
        perfil_cliente=state_values.get("perfil_cliente"),
        profile_status=state_values.get("profile_status"),
        cliente_priorizado_contexto=state_values.get("cliente_priorizado_contexto"),
        inteligencia_sector=state_values.get("inteligencia_sector"),
        human_insights=state_values.get("human_insights", []),
        propuesta_final=state_values.get("propuesta_final"),
        status=resolved_status,
        warning=state_values.get("warning"),
        error=state_values.get("error"),
    )


def enforce_rate_limit(scope: str, key: str, limit: int) -> None:
    result = rate_limiter.check(
        key=f"{scope}:{key}",
        limit=max(1, int(limit)),
        window_sec=max(1, int(settings.rate_limit_window_sec)),
    )
    if result.allowed:
        return
    raise HTTPException(
        status_code=429,
        detail={
            "code": "RATE_LIMITED",
            "message": (
                f"Demasiadas solicitudes para {scope}. "
                f"Intenta de nuevo en {result.retry_after_sec}s."
            ),
            "retry_after_sec": result.retry_after_sec,
        },
    )


async def invoke_llm_async(prompt: str) -> str:
    """Invoke the shared chat LLM asynchronously with timeout."""
    llm = get_chat_llm()
    try:
        if hasattr(llm, "ainvoke"):
            response = await asyncio.wait_for(
                llm.ainvoke(prompt),
                timeout=_LLM_TIMEOUT_SEC,
            )
        else:
            response = llm.invoke(prompt)
    except asyncio.TimeoutError as exc:
        raise ExternalDependencyTimeout("Gemini", _LLM_TIMEOUT_SEC) from exc
    return str(getattr(response, "content", response)).strip()
