"""
main.py — FastAPI MVP V2 Backend
Refactored to support LangGraph HITL flow, Redis persistence, and Peru profiles.
"""
import uuid
import logging
import csv
import io
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Literal, List
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from src.agent.graph import graph
from src.api.intel import router as intel_router
from src.config import get_settings
from src.services.errors import (
    BackendDomainError,
    BusinessRuleError,
    ExternalDependencyTimeout,
    SessionNotFoundError,
)
from src.services.metrics import search_metrics
from src.services.intel_metrics import intel_metrics
from src.services.chat_audit import chat_audit_store
from src.services.chat_alerts import ChatAlertThresholds, build_chat_alerts
from src.services.chat_guardrails import evaluate_chat_message
from src.services.rate_limit import rate_limiter
from src.services.session_funnel import session_funnel_store
from src.services.prioritized_clients import (
    get_prioritized_clients_catalog,
    get_prioritized_client_context,
    get_prioritized_clients,
    is_prioritized_client,
    normalize_company_name,
)
from src.services.proposal_context import (
    filter_selected_cases,
    format_cases_for_prompt,
    validate_selected_cases_have_url,
)
from src.services.search_service import search_cases_with_sla
from src.tools.qdrant_tool import db_connection
from langchain_google_genai import ChatGoogleGenerativeAI

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neo_api_v2")
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialization logic (if any specific cleanup is needed)
    logger.info("🚀 NEO Proposal Agent API V2 starting up...")
    yield
    logger.info("🛑 NEO Proposal Agent API V2 shutting down...")

app = FastAPI(
    title="NEO Proposal Agent API",
    version="2.0.0",
    description="Backend para la generación de propuestas comerciales orientadas a perfiles corporativos.",
    lifespan=lifespan
)
app.include_router(intel_router, prefix="/intel", tags=["intel"])

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class StartRequest(BaseModel):
    empresa: str = Field(..., example="BCP")
    rubro: str = Field(..., example="Banca")
    area: str = Field(..., example="Operaciones")
    problema: str = Field(..., min_length=20, example="Automatización de conciliaciones bancarias...")
    switch: Literal["neo", "ai", "both"] = "both"

    @field_validator("switch", mode="before")
    @classmethod
    def normalize_switch(cls, value: str) -> str:
        return str(value).strip().lower()

class SelectRequest(BaseModel):
    case_ids: List[str] = Field(..., min_items=1)

class SearchRequest(BaseModel):
    problema: str = Field(..., min_length=10, example="Mejorar decisiones en credit scoring con IA")
    switch: Literal["neo", "ai", "both"] = "both"

    @field_validator("switch", mode="before")
    @classmethod
    def normalize_switch(cls, value: str) -> str:
        return str(value).strip().lower()

class RefineRequest(BaseModel):
    instruction: str = Field(..., min_length=5, example="Hazla más corta y enfatiza ROI")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, example="Que caso aplica mejor para este cliente y por que?")

class ChatResponse(BaseModel):
    thread_id: str
    answer: str
    used_case_ids: List[str] = Field(default_factory=list)
    used_case_count: int
    status: str
    guardrail_code: Optional[str] = None
    audit_ts_utc: Optional[str] = None

class IngestRequest(BaseModel):
    csv_files: List[str] = Field(default_factory=lambda: ["ai_cases.csv", "neo_legacy.csv"])
    force_rebuild: bool = False

class AgentStateResponse(BaseModel):
    thread_id: str
    empresa: str
    area: str
    problema: str
    casos_encontrados: List[dict]
    neo_cases: List[dict] = Field(default_factory=list)
    ai_cases: List[dict] = Field(default_factory=list)
    top_match_global: Optional[dict] = None
    top_match_global_reason: Optional[str] = None
    casos_seleccionados_ids: List[str]
    perfil_cliente: Optional[dict] = None
    profile_status: Optional[Literal["found", "not_found", "incomplete"]] = None
    cliente_priorizado_contexto: Optional[dict] = None
    inteligencia_sector: Optional[dict] = None
    human_insights: List[dict] = Field(default_factory=list)
    propuesta_final: Optional[str] = None
    status: str
    error: Optional[str] = None


def _raise_domain_http(error: BackendDomainError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )


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

# --- Endpoints ---

@app.get("/health")
async def health():
    """Verifica el estado de los servicios."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.app_env,
        "qdrant": "connected", # Podríamos añadir un ping real aquí
        "redis_required": settings.is_non_local_env,
    }


@app.get("/api/prioritized-clients")
async def prioritized_clients():
    """Lista oficial de clientes priorizados para fase actual."""
    catalog = get_prioritized_clients_catalog()
    return {
        "status": "success",
        "total": len(catalog),
        "clients": get_prioritized_clients(),
        "catalog": catalog,
    }

@app.post("/api/search")
async def api_search(data: SearchRequest):
    """
    Primitiva de búsqueda semántica.
    Stateless y reutilizable por orquestadores (/agent/*).
    """
    try:
        payload = await search_cases_with_sla(
            problema=data.problema.strip(),
            switch=data.switch,
            limit=6,
            score_threshold=0.50,
        )
        search_metrics.record_success(
            total_ms=payload.get("latencia_ms", 0),
            embedding_ms=payload.get("embedding_ms"),
            qdrant_ms=payload.get("qdrant_ms"),
            cache_hit=payload.get("cache_hit"),
        )
        return payload
    except ExternalDependencyTimeout as exc:
        search_metrics.record_error(exc.code)
        _raise_domain_http(exc)
    except BackendDomainError as exc:
        search_metrics.record_error(exc.code)
        _raise_domain_http(exc)
    except Exception as exc:
        search_metrics.record_error("UNHANDLED_ERROR")
        logger.exception("Error in /api/search: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/ops/metrics")
async def get_ops_metrics(authorization: str | None = Header(default=None)):
    """
    Métricas operativas livianas para seguimiento de SLA de búsqueda.
    En no-local exige ADMIN_TOKEN.
    """
    _require_admin_access(authorization)

    return {
        "status": "ok",
        "environment": settings.app_env,
        "search": search_metrics.snapshot(),
        "intel": intel_metrics.snapshot(),
    }

@app.get("/ops/chat-audit")
async def get_chat_audit(
    authorization: str | None = Header(default=None),
    limit: int = 100,
    status: str | None = None,
):
    """
    Traza operativa de chat/guardrails para auditoria.
    """
    _require_admin_access(authorization)
    return {
        "status": "ok",
        "environment": settings.app_env,
        "chat_audit": chat_audit_store.snapshot(limit=limit, status=status),
    }


@app.get("/ops/chat-audit/export")
async def export_chat_audit(
    authorization: str | None = Header(default=None),
    format: Literal["json", "csv"] = "json",
    limit: int = 200,
    status: str | None = None,
):
    """
    Exporta trazas operativas de chat en JSON/CSV para analisis externo.
    """
    _require_admin_access(authorization)
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
            "ts_utc",
            "thread_id",
            "status",
            "guardrail_code",
            "used_case_count",
            "used_case_ids",
            "message_preview",
        ],
    )
    writer.writeheader()
    for row in snap.get("items", []):
        writer.writerow(
            {
                "ts_utc": row.get("ts_utc", ""),
                "thread_id": row.get("thread_id", ""),
                "status": row.get("status", ""),
                "guardrail_code": row.get("guardrail_code", ""),
                "used_case_count": row.get("used_case_count", 0),
                "used_case_ids": ",".join(str(v) for v in row.get("used_case_ids", [])),
                "message_preview": row.get("message_preview", ""),
            }
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="chat_audit_export.csv"'},
    )


@app.get("/ops/chat-analytics")
async def get_chat_analytics(
    authorization: str | None = Header(default=None),
    status: str | None = None,
):
    """
    KPIs operativos de chat contextual y guardrails.
    """
    _require_admin_access(authorization)
    return {
        "status": "ok",
        "environment": settings.app_env,
        "chat_analytics": chat_audit_store.analytics(status=status),
    }


@app.get("/ops/chat-alerts")
async def get_chat_alerts(
    authorization: str | None = Header(default=None),
    status: str | None = None,
):
    """
    Alertas operativas automáticas sobre analítica de chat.
    """
    _require_admin_access(authorization)
    analytics = chat_audit_store.analytics(status=status)
    thresholds = ChatAlertThresholds(
        min_events=settings.chat_alert_min_events,
        block_rate_warning=settings.chat_alert_block_rate_warning,
        block_rate_critical=settings.chat_alert_block_rate_critical,
        no_case_usage_warning=settings.chat_alert_no_case_usage_warning,
        company_concentration_warning=settings.chat_alert_company_concentration_warning,
    )
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


@app.get("/ops/chat-alerts/history")
async def get_chat_alerts_history(
    authorization: str | None = Header(default=None),
    bucket: Literal["hour", "day"] = "hour",
    limit_buckets: int = 48,
    status: str | None = None,
):
    """
    Historial temporal de alertas de chat para analisis de tendencia.
    """
    _require_admin_access(authorization)
    thresholds = ChatAlertThresholds(
        min_events=settings.chat_alert_min_events,
        block_rate_warning=settings.chat_alert_block_rate_warning,
        block_rate_critical=settings.chat_alert_block_rate_critical,
        no_case_usage_warning=settings.chat_alert_no_case_usage_warning,
        company_concentration_warning=settings.chat_alert_company_concentration_warning,
    )
    history = chat_audit_store.analytics_history(
        bucket=bucket,
        limit_buckets=limit_buckets,
        status=status,
    )
    enriched_series: list[dict] = []
    for item in history.get("series", []):
        metrics = item.get("metrics", {})
        enriched_series.append(
            {
                "bucket_start_utc": item.get("bucket_start_utc"),
                "metrics": metrics,
                "alerts": build_chat_alerts(metrics, thresholds),
            }
        )

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


@app.get("/ops/funnel")
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
    """
    Conversión operativa del flujo MVP por sesiones (thread).
    """
    _require_admin_access(authorization)
    safe_page = max(1, int(page))
    safe_page_size = max(1, min(int(page_size), 200))
    offset = (safe_page - 1) * safe_page_size
    now_utc = datetime.now(timezone.utc)
    updated_after_utc: str | None = None
    if time_range == "1h":
        updated_after_utc = (now_utc - timedelta(hours=1)).isoformat()
    elif time_range == "24h":
        updated_after_utc = (now_utc - timedelta(hours=24)).isoformat()
    elif time_range == "7d":
        updated_after_utc = (now_utc - timedelta(days=7)).isoformat()

    funnel_summary = session_funnel_store.summary(
        company=company,
        updated_after_utc=updated_after_utc,
        completed_only=completed_only,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    sessions = session_funnel_store.snapshot(
        limit=safe_page_size,
        offset=offset,
        company=company,
        updated_after_utc=updated_after_utc,
        completed_only=completed_only,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return {
        "status": "ok",
        "environment": settings.app_env,
        "query": {
            "company": company,
            "time_range": time_range,
            "completed_only": completed_only,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
            "page": safe_page,
            "page_size": safe_page_size,
            "offset": offset,
        },
        "funnel": funnel_summary,
        "sessions": sessions,
    }


@app.get("/ops/funnel/export")
async def export_ops_funnel(
    authorization: str | None = Header(default=None),
    format: Literal["json", "csv"] = "csv",
    company: str | None = None,
    time_range: Literal["1h", "24h", "7d", "all"] = "24h",
    completed_only: bool = False,
    sort_by: str = "last_update_utc",
    sort_dir: Literal["asc", "desc"] = "desc",
):
    """
    Exporta sesiones de funnel con filtros server-side.
    """
    _require_admin_access(authorization)
    now_utc = datetime.now(timezone.utc)
    updated_after_utc: str | None = None
    if time_range == "1h":
        updated_after_utc = (now_utc - timedelta(hours=1)).isoformat()
    elif time_range == "24h":
        updated_after_utc = (now_utc - timedelta(hours=24)).isoformat()
    elif time_range == "7d":
        updated_after_utc = (now_utc - timedelta(days=7)).isoformat()

    snap = session_funnel_store.snapshot(
        limit=5000,
        offset=0,
        company=company,
        updated_after_utc=updated_after_utc,
        completed_only=completed_only,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    if format == "json":
        return {
            "status": "ok",
            "environment": settings.app_env,
            "query": {
                "company": company,
                "time_range": time_range,
                "completed_only": completed_only,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
            },
            "sessions": snap,
        }

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "thread_id",
            "empresa",
            "area",
            "total_cases",
            "selected_count",
            "proposal_generated",
            "refined_count",
            "chat_count",
            "guardrail_blocked_count",
            "started_at_utc",
            "last_update_utc",
        ],
    )
    writer.writeheader()
    for row in snap.get("items", []):
        writer.writerow(
            {
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
            }
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="ops_funnel_export.csv"'},
    )


@app.get("/ops/funnel/history")
async def get_ops_funnel_history(
    authorization: str | None = Header(default=None),
    bucket: Literal["hour", "day"] = "hour",
    limit_buckets: int = 48,
    company: str | None = None,
    time_range: Literal["1h", "24h", "7d", "all"] = "24h",
    completed_only: bool = False,
):
    """
    Historial temporal del funnel para detectar tendencia de conversión.
    """
    _require_admin_access(authorization)
    now_utc = datetime.now(timezone.utc)
    updated_after_utc: str | None = None
    if time_range == "1h":
        updated_after_utc = (now_utc - timedelta(hours=1)).isoformat()
    elif time_range == "24h":
        updated_after_utc = (now_utc - timedelta(hours=24)).isoformat()
    elif time_range == "7d":
        updated_after_utc = (now_utc - timedelta(days=7)).isoformat()

    history = session_funnel_store.history(
        bucket=bucket,
        limit_buckets=limit_buckets,
        company=company,
        updated_after_utc=updated_after_utc,
        completed_only=completed_only,
    )
    return {
        "status": "ok",
        "environment": settings.app_env,
        "query": {
            "bucket": bucket,
            "limit_buckets": max(1, min(int(limit_buckets), 720)),
            "company": company,
            "time_range": time_range,
            "completed_only": completed_only,
        },
        "history": history,
    }

@app.post("/agent/start", response_model=AgentStateResponse)
async def start_agent(data: StartRequest):
    """
    Inicia una nueva sesión de generación de propuesta.
    Ejecuta el grafo hasta el nodo de selección (HITL).
    """
    _enforce_rate_limit(
        "start",
        key=normalize_company_name(data.empresa),
        limit=settings.rate_limit_start_per_window,
    )
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    empresa_normalized = normalize_company_name(data.empresa)
    if not is_prioritized_client(data.empresa):
        _raise_domain_http(
            BusinessRuleError(
                "En esta fase solo se permiten clientes priorizados para generar propuestas."
            )
        )
    
    inputs = {
        "empresa": empresa_normalized,
        "rubro": data.rubro,
        "area": data.area,
        "problema": data.problema,
        "switch": data.switch,
        "cliente_priorizado_contexto": get_prioritized_client_context(data.empresa),
        "casos_seleccionados_ids": [],
        "propuesta_versiones": []
    }
    
    try:
        # Ejecutamos el grafo. Se detendrá antes de 'draft_node' debido a interrupt_before
        final_state = await graph.ainvoke(inputs, config=config)
        session_funnel_store.record_start(
            thread_id=thread_id,
            empresa=empresa_normalized,
            area=data.area,
            total_cases=len(final_state.get("casos_encontrados", [])),
        )
        return _map_state_response(thread_id, final_state, status="awaiting_selection")
    except BackendDomainError as exc:
        _raise_domain_http(exc)
    except Exception as e:
        logger.exception(f"Error starting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest")
async def ingest_cases(data: IngestRequest, authorization: str | None = Header(default=None)):
    """
    Endpoint administrativo de ingesta de casos hacia Qdrant.
    Si ADMIN_TOKEN está configurado, exige header Authorization Bearer.
    """
    _require_admin_access(authorization)

    base = Path(__file__).resolve().parents[3] / "data"
    csv_paths = [str(base / name) for name in data.csv_files]
    missing = [p for p in csv_paths if not Path(p).exists()]
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV no encontrados: {missing}")

    try:
        import asyncio
        if data.force_rebuild:
            await asyncio.to_thread(db_connection.reset_cases_collection, "neo_cases_v1")
        ingest_summary = await asyncio.to_thread(db_connection.load_csv_files, csv_paths, "neo_cases_v1")
    except Exception as exc:
        logger.exception("Error en /api/ingest: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "status": "success",
        "summary": {
            "csv_files": data.csv_files,
            "inserted": ingest_summary.get("valid", 0),
            "rejected": ingest_summary.get("rejected", 0),
            "with_url": ingest_summary.get("with_url", 0),
            "missing_url": ingest_summary.get("missing_url", 0),
            "source_stats": ingest_summary.get("source_stats", {}),
            "collection": "neo_cases_v1",
        },
    }

@app.post("/agent/{thread_id}/select", response_model=AgentStateResponse)
async def select_cases(thread_id: str, data: SelectRequest):
    """
    Recibe la selección de casos del usuario y genera la propuesta final.
    """
    _enforce_rate_limit(
        "select",
        key=thread_id,
        limit=settings.rate_limit_select_per_window,
    )
    config = {"configurable": {"thread_id": thread_id}}
    
    # 1. Verificar que el estado existe
    current_state = await graph.aget_state(config)
    if not current_state.values:
        _raise_domain_http(SessionNotFoundError("Sesión no encontrada."))
    
    try:
        current_values = current_state.values or {}
        all_cases = current_values.get("casos_encontrados", [])
        available_ids = {str(case.get("id")) for case in all_cases}
        invalid_ids = [case_id for case_id in data.case_ids if case_id not in available_ids]
        if invalid_ids:
            _raise_domain_http(
                BusinessRuleError(
                    f"Hay case_ids que no pertenecen a la busqueda actual: {', '.join(invalid_ids)}"
                )
            )

        selected_cases = filter_selected_cases(all_cases, data.case_ids)
        has_url, missing_url_ids = validate_selected_cases_have_url(selected_cases)
        if not has_url:
            _raise_domain_http(
                BusinessRuleError(
                    "Cada ficha seleccionada debe tener URL de evidencia. "
                    f"Faltan URL en: {', '.join(missing_url_ids)}"
                )
            )

        # 2. Actualizar el estado con los IDs seleccionados
        await graph.aupdate_state(config, {"casos_seleccionados_ids": data.case_ids})
        
        # 3. Continuar la ejecución del grafo
        final_state = await graph.ainvoke(None, config=config)
        session_funnel_store.record_select(
            thread_id=thread_id,
            selected_count=len(data.case_ids),
            completed=bool(final_state.get("propuesta_final")),
        )
        return _map_state_response(thread_id, final_state, status="completed")
    except BackendDomainError as exc:
        _raise_domain_http(exc)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in select_cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/{thread_id}/refine", response_model=AgentStateResponse)
async def refine_proposal(thread_id: str, data: RefineRequest):
    """
    Refina la propuesta existente manteniendo contexto de sesión.
    """
    _enforce_rate_limit(
        "refine",
        key=thread_id,
        limit=settings.rate_limit_refine_per_window,
    )
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    if not state.values:
        _raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    v = state.values
    if not v.get("propuesta_final"):
        _raise_domain_http(BusinessRuleError("No hay propuesta previa para refinar."))

    try:
        app_settings = get_settings()
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=app_settings.gemini_api_key,
        )
        selected_cases = filter_selected_cases(
            list(v.get("casos_encontrados", [])),
            list(v.get("casos_seleccionados_ids", [])),
        )
        profile_context = v.get("perfil_cliente") or {}
        client_context = v.get("cliente_priorizado_contexto") or {}
        sector_context = v.get("inteligencia_sector") or {}

        prompt = (
            "Refina la siguiente propuesta comercial manteniendo precisión y tono ejecutivo.\n"
            "Aplica estrictamente la instrucción del usuario.\n\n"
            "--- CONTEXTO CLIENTE PRIORIZADO ---\n"
            f"Empresa: {v.get('empresa', 'N/A')}\n"
            f"Vertical: {client_context.get('vertical', 'N/A')}\n"
            f"Prioridades: {client_context.get('priorities', [])}\n"
            f"Restricciones: {client_context.get('constraints', [])}\n\n"
            "--- CONTEXTO PERFIL CLIENTE ---\n"
            f"Objetivos: {profile_context.get('objetivos', [])}\n"
            f"Pain points: {profile_context.get('pain_points', [])}\n"
            f"Notas: {profile_context.get('notas', 'N/A')}\n\n"
            "--- CONTEXTO SECTOR ---\n"
            f"Industria: {sector_context.get('industria', 'N/A')} / Area: {sector_context.get('area', 'N/A')}\n"
            f"Tendencias: {sector_context.get('tendencias', [])}\n\n"
            "--- CASOS SELECCIONADOS CON EVIDENCIA ---\n"
            f"{format_cases_for_prompt(selected_cases)}\n\n"
            f"INSTRUCCION: {data.instruction}\n\n"
            "PROPUESTA ACTUAL:\n"
            f"{v['propuesta_final']}\n"
        )
        response = llm.invoke(prompt)
        refined = str(response.content).strip()

        versions = list(v.get("propuesta_versiones") or [])
        versions.append(refined)
        await graph.aupdate_state(
            config,
            {
                "propuesta_final": refined,
                "propuesta_versiones": versions,
                "error": "",
            },
        )

        new_state = await graph.aget_state(config)
        latest = new_state.values
        session_funnel_store.record_refine(thread_id)
        return _map_state_response(thread_id, latest, status="completed")
    except BackendDomainError as exc:
        _raise_domain_http(exc)
    except Exception as exc:
        logger.exception("Error refining proposal: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/agent/{thread_id}/chat", response_model=ChatResponse)
async def contextual_chat(thread_id: str, data: ChatRequest):
    """
    Chat contextual dedicado por thread.
    Usa contexto de cliente priorizado, perfil, sector y casos para responder con valor comercial.
    """
    _enforce_rate_limit(
        "chat",
        key=thread_id,
        limit=settings.rate_limit_chat_per_window,
    )
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    if not state.values:
        _raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    v = state.values
    all_cases = list(v.get("casos_encontrados", []))
    selected_ids = list(v.get("casos_seleccionados_ids", []))
    selected_cases = filter_selected_cases(all_cases, selected_ids)
    cases_for_chat = selected_cases if selected_cases else all_cases[:3]
    used_case_ids = [str(c.get("id")) for c in cases_for_chat if c.get("id")]

    profile_context = v.get("perfil_cliente") or {}
    client_context = v.get("cliente_priorizado_contexto") or {}
    sector_context = v.get("inteligencia_sector") or {}
    chat_history = list(v.get("chat_messages") or [])
    history_tail = chat_history[-8:]
    history_block = "\n".join(
        f"{item.get('role', 'user').upper()}: {item.get('content', '')}" for item in history_tail
    )
    audit_ts = datetime.now(timezone.utc).isoformat()
    guardrail = evaluate_chat_message(data.message)

    if not guardrail.allowed:
        blocked_answer = (
            "No puedo procesar ese mensaje en el chat contextual por una regla de seguridad. "
            "Reformula tu consulta enfocandola en estrategia, evidencia de casos o propuesta de valor."
        )
        new_history = history_tail + [
            {"role": "user", "content": guardrail.sanitized_message},
            {"role": "assistant", "content": blocked_answer},
        ]
        await graph.aupdate_state(config, {"chat_messages": new_history})
        chat_audit_store.record_event(
            thread_id=thread_id,
            empresa=v.get("empresa"),
            status="guardrail_blocked",
            guardrail_code=guardrail.code,
            used_case_ids=[],
            message=guardrail.sanitized_message,
        )
        session_funnel_store.record_chat(thread_id=thread_id, status="guardrail_blocked")
        return ChatResponse(
            thread_id=thread_id,
            answer=blocked_answer,
            used_case_ids=[],
            used_case_count=0,
            status="guardrail_blocked",
            guardrail_code=guardrail.code,
            audit_ts_utc=audit_ts,
        )

    try:
        app_settings = get_settings()
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=app_settings.gemini_api_key,
        )
        prompt = (
            "Eres el asistente contextual de propuestas NEO.\n"
            "Responde con foco comercial, claridad ejecutiva y trazabilidad a casos.\n"
            "Si recomiendas una linea de propuesta, indica por que aporta valor al cliente.\n"
            "No inventes evidencias; usa solo el contexto provisto.\n\n"
            "--- CONTEXTO CLIENTE PRIORIZADO ---\n"
            f"Empresa: {v.get('empresa', 'N/A')}\n"
            f"Vertical: {client_context.get('vertical', 'N/A')}\n"
            f"Prioridades: {client_context.get('priorities', [])}\n"
            f"Restricciones: {client_context.get('constraints', [])}\n\n"
            "--- PERFIL CLIENTE ---\n"
            f"Objetivos: {profile_context.get('objetivos', [])}\n"
            f"Pain points: {profile_context.get('pain_points', [])}\n"
            f"Notas: {profile_context.get('notas', 'N/A')}\n\n"
            "--- CONTEXTO SECTOR ---\n"
            f"Industria: {sector_context.get('industria', 'N/A')} / Area: {sector_context.get('area', 'N/A')}\n"
            f"Tendencias: {sector_context.get('tendencias', [])}\n\n"
            "--- CASOS DISPONIBLES PARA RESPONDER ---\n"
            f"{format_cases_for_prompt(cases_for_chat)}\n\n"
            "--- HISTORIAL RECIENTE ---\n"
            f"{history_block or 'Sin historial previo.'}\n\n"
            "--- MENSAJE DEL CONSULTOR ---\n"
            f"{guardrail.sanitized_message}\n\n"
            "Responde en maximo 180 palabras y cita IDs de casos cuando corresponda."
        )
        response = llm.invoke(prompt)
        answer = str(response.content).strip()

        new_history = history_tail + [
            {"role": "user", "content": guardrail.sanitized_message},
            {"role": "assistant", "content": answer},
        ]
        await graph.aupdate_state(config, {"chat_messages": new_history})
        chat_audit_store.record_event(
            thread_id=thread_id,
            empresa=v.get("empresa"),
            status="ok",
            guardrail_code=guardrail.code,
            used_case_ids=used_case_ids,
            message=guardrail.sanitized_message,
        )
        session_funnel_store.record_chat(thread_id=thread_id, status="ok")

        return ChatResponse(
            thread_id=thread_id,
            answer=answer,
            used_case_ids=used_case_ids,
            used_case_count=len(used_case_ids),
            status="ok",
            guardrail_code=guardrail.code,
            audit_ts_utc=audit_ts,
        )
    except BackendDomainError as exc:
        _raise_domain_http(exc)
    except Exception as exc:
        logger.exception("Error in contextual chat: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/agent/{thread_id}/state", response_model=AgentStateResponse)
async def get_agent_state(thread_id: str):
    """Recupera el estado actual de una sesión."""
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    
    if not state.values:
        _raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    return _map_state_response(thread_id, state.values)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
