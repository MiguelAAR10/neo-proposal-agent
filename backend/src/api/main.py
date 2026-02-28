"""
main.py — FastAPI MVP V2 Backend
Refactored to support LangGraph HITL flow, Redis persistence, and Peru profiles.
"""
import uuid
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Literal, List

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from src.agent.graph import graph
from src.config import get_settings
from src.services.errors import (
    BackendDomainError,
    BusinessRuleError,
    ExternalDependencyTimeout,
    SessionNotFoundError,
)
from src.services.metrics import search_metrics
from src.services.prioritized_clients import (
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
    propuesta_final: Optional[str] = None
    status: str
    error: Optional[str] = None


def _raise_domain_http(error: BackendDomainError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )


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
        propuesta_final=state_values.get("propuesta_final"),
        status=resolved_status,
        error=state_values.get("error"),
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
    return {
        "status": "success",
        "total": len(get_prioritized_clients()),
        "clients": get_prioritized_clients(),
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
    if settings.is_non_local_env and not settings.admin_token:
        raise HTTPException(
            status_code=500,
            detail={"code": "MISCONFIGURATION", "message": "ADMIN_TOKEN obligatorio en staging/prod."},
        )
    if settings.admin_token:
        expected = f"Bearer {settings.admin_token}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Unauthorized"})

    return {
        "status": "ok",
        "environment": settings.app_env,
        "search": search_metrics.snapshot(),
    }

@app.post("/agent/start", response_model=AgentStateResponse)
async def start_agent(data: StartRequest):
    """
    Inicia una nueva sesión de generación de propuesta.
    Ejecuta el grafo hasta el nodo de selección (HITL).
    """
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
    if settings.is_non_local_env and not settings.admin_token:
        raise HTTPException(
            status_code=500,
            detail={"code": "MISCONFIGURATION", "message": "ADMIN_TOKEN obligatorio en staging/prod."},
        )

    if settings.admin_token:
        expected = f"Bearer {settings.admin_token}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Unauthorized"})

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
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    if not state.values:
        _raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    v = state.values
    if not v.get("propuesta_final"):
        _raise_domain_http(BusinessRuleError("No hay propuesta previa para refinar."))

    try:
        settings = get_settings()
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=settings.gemini_api_key,
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
        return _map_state_response(thread_id, latest, status="completed")
    except BackendDomainError as exc:
        _raise_domain_http(exc)
    except Exception as exc:
        logger.exception("Error refining proposal: %s", exc)
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
