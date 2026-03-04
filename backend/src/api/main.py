"""
main.py — FastAPI MVP V2 Backend entrypoint.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import redis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.agent.graph import graph
from src.api.intel import router as intel_router
from src.api.routers import admin_router, agent_router, ops_router
from src.api.schemas import (
    AgentStateResponse,
    ChatRequest,
    ChatResponse,
    IngestRequest,
    RefineRequest,
    SearchRequest,
    SelectRequest,
    StartRequest,
)
from src.config import get_settings
from src.services.chat_audit import chat_audit_store
from src.services.chat_guardrails import evaluate_chat_message
from src.services.errors import BackendDomainError, ExternalDependencyTimeout
from src.services.intel_metrics import intel_metrics
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
from langchain_google_genai import ChatGoogleGenerativeAI

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neo_api_v2")
settings = get_settings()
_INTERNAL_SERVER_ERROR_DETAIL = {"error": "Internal Server Error", "code": 500}
_HEALTHCHECK_TIMEOUT_SEC = 1.0
_LLM_TIMEOUT_SEC = 20.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 NEO Proposal Agent API V2 starting up...")
    yield
    logger.info("🛑 NEO Proposal Agent API V2 shutting down...")


app = FastAPI(
    title="NEO Proposal Agent API",
    version="2.0.0",
    description="Backend para la generación de propuestas comerciales orientadas a perfiles corporativos.",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Shared helpers used by routers ---
def _raise_domain_http(error: BackendDomainError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )


def _raise_internal_server_error(message: str) -> None:
    logger.exception(message)
    raise HTTPException(status_code=500, detail=_INTERNAL_SERVER_ERROR_DETAIL)


def _require_admin_access(authorization: str | None) -> None:
    if settings.is_non_local_env and not settings.admin_token:
        raise HTTPException(
            status_code=500,
            detail={"code": "MISCONFIGURATION", "message": "ADMIN_TOKEN obligatorio en staging/prod."},
        )
    if settings.admin_token:
        expected = f"Bearer {settings.admin_token}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Unauthorized"})


def _map_state_response(
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


def _enforce_rate_limit(scope: str, key: str, limit: int) -> None:
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


async def _invoke_llm_async(llm: ChatGoogleGenerativeAI, prompt: str) -> str:
    """Invoke LLM asynchronously; fallback path is only for legacy mocks/tests."""
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


async def _check_qdrant_health() -> str:
    if not settings.qdrant_url:
        return "not_configured"
    try:
        await asyncio.wait_for(
            asyncio.to_thread(lambda: db_connection._ensure_client().get_collections()),
            timeout=_HEALTHCHECK_TIMEOUT_SEC,
        )
        return "connected"
    except Exception as exc:
        logger.warning("Qdrant health check failed: %s", exc)
        return "unavailable"


async def _check_redis_health() -> str:
    if not settings.redis_url:
        return "not_configured"

    def _ping() -> bool:
        client = redis.from_url(
            settings.redis_url,
            socket_timeout=_HEALTHCHECK_TIMEOUT_SEC,
            socket_connect_timeout=_HEALTHCHECK_TIMEOUT_SEC,
            decode_responses=True,
        )
        return bool(client.ping())

    try:
        ok = await asyncio.wait_for(
            asyncio.to_thread(_ping),
            timeout=_HEALTHCHECK_TIMEOUT_SEC,
        )
        return "connected" if ok else "unavailable"
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        return "unavailable"


# --- Base endpoints in entrypoint ---
@app.get("/health")
async def health():
    """Verifica el estado de los servicios."""
    qdrant_status, redis_status = await asyncio.gather(
        _check_qdrant_health(),
        _check_redis_health(),
    )
    status = "healthy" if (qdrant_status == "connected" and redis_status == "connected") else "degraded"
    return {
        "status": status,
        "version": "2.0.0",
        "environment": settings.app_env,
        "qdrant": qdrant_status,
        "redis_required": settings.is_non_local_env,
    }


# --- Router registration ---
app.include_router(agent_router)
app.include_router(ops_router)
app.include_router(admin_router)
app.include_router(intel_router, prefix="/intel", tags=["intel"])


# --- Backward-compatible symbol exports for existing tests/consumers ---
from src.api.routers.admin import ingest_cases
from src.api.routers.agent import (
    api_search,
    contextual_chat,
    get_agent_state,
    prioritized_clients,
    refine_proposal,
    select_cases,
    start_agent,
)
from src.api.routers.ops import (
    export_chat_audit,
    export_ops_funnel,
    get_chat_alerts,
    get_chat_alerts_history,
    get_chat_analytics,
    get_chat_audit,
    get_ops_funnel,
    get_ops_funnel_history,
    get_ops_metrics,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
