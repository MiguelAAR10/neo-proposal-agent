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
from src.services.search_service import search_cases_with_sla
from src.tools.qdrant_tool import db_connection
from langchain_google_genai import ChatGoogleGenerativeAI

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neo_api_v2")

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
    allow_origins=["*"], # En producción, restringir a dominios específicos
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
    propuesta_final: Optional[str] = None
    status: str
    error: Optional[str] = None

# --- Endpoints ---

@app.get("/health")
async def health():
    """Verifica el estado de los servicios."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "qdrant": "connected" # Podríamos añadir un ping real aquí
    }

@app.post("/api/search")
async def api_search(data: SearchRequest):
    """
    Primitiva de búsqueda semántica.
    Stateless y reutilizable por orquestadores (/agent/*).
    """
    try:
        return await search_cases_with_sla(
            problema=data.problema.strip(),
            switch=data.switch,
            limit=6,
            score_threshold=0.50,
        )
    except TimeoutError as exc:
        detail = str(exc)
        status = 503 if "Qdrant" in detail else 504
        raise HTTPException(status_code=status, detail=detail)
    except Exception as exc:
        logger.exception("Error in /api/search: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/agent/start", response_model=AgentStateResponse)
async def start_agent(data: StartRequest):
    """
    Inicia una nueva sesión de generación de propuesta.
    Ejecuta el grafo hasta el nodo de selección (HITL).
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    inputs = {
        "empresa": data.empresa,
        "rubro": data.rubro,
        "area": data.area,
        "problema": data.problema,
        "switch": data.switch,
        "casos_seleccionados_ids": [],
        "propuesta_versiones": []
    }
    
    try:
        # Ejecutamos el grafo. Se detendrá antes de 'draft_node' debido a interrupt_before
        final_state = await graph.ainvoke(inputs, config=config)
        
        return AgentStateResponse(
            thread_id=thread_id,
            empresa=final_state["empresa"],
            area=final_state["area"],
            problema=final_state["problema"],
            casos_encontrados=final_state.get("casos_encontrados", []),
            neo_cases=final_state.get("neo_cases", []),
            ai_cases=final_state.get("ai_cases", []),
            top_match_global=final_state.get("top_match_global"),
            top_match_global_reason=final_state.get("top_match_global_reason"),
            casos_seleccionados_ids=final_state.get("casos_seleccionados_ids", []),
            perfil_cliente=final_state.get("perfil_cliente"),
            propuesta_final=final_state.get("propuesta_final"),
            status="awaiting_selection",
            error=final_state.get("error")
        )
    except Exception as e:
        logger.exception(f"Error starting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest")
async def ingest_cases(data: IngestRequest, authorization: str | None = Header(default=None)):
    """
    Endpoint administrativo de ingesta de casos hacia Qdrant.
    Si ADMIN_TOKEN está configurado, exige header Authorization Bearer.
    """
    settings = get_settings()
    if settings.admin_token:
        expected = f"Bearer {settings.admin_token}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    base = Path(__file__).resolve().parents[3] / "data"
    csv_paths = [str(base / name) for name in data.csv_files]
    missing = [p for p in csv_paths if not Path(p).exists()]
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV no encontrados: {missing}")

    try:
        import asyncio
        if data.force_rebuild:
            await asyncio.to_thread(db_connection.reset_cases_collection, "neo_cases_v1")
        inserted = await asyncio.to_thread(db_connection.load_csv_files, csv_paths, "neo_cases_v1")
    except Exception as exc:
        logger.exception("Error en /api/ingest: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "status": "success",
        "summary": {
            "csv_files": data.csv_files,
            "inserted": inserted,
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
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    
    try:
        # 2. Actualizar el estado con los IDs seleccionados
        await graph.aupdate_state(config, {"casos_seleccionados_ids": data.case_ids})
        
        # 3. Continuar la ejecución del grafo
        final_state = await graph.ainvoke(None, config=config)
        
        return AgentStateResponse(
            thread_id=thread_id,
            empresa=final_state["empresa"],
            area=final_state["area"],
            problema=final_state["problema"],
            casos_encontrados=final_state.get("casos_encontrados", []),
            neo_cases=final_state.get("neo_cases", []),
            ai_cases=final_state.get("ai_cases", []),
            top_match_global=final_state.get("top_match_global"),
            top_match_global_reason=final_state.get("top_match_global_reason"),
            casos_seleccionados_ids=final_state.get("casos_seleccionados_ids", []),
            perfil_cliente=final_state.get("perfil_cliente"),
            propuesta_final=final_state.get("propuesta_final"),
            status="completed",
            error=final_state.get("error")
        )
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
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")

    v = state.values
    if not v.get("propuesta_final"):
        raise HTTPException(status_code=400, detail="No hay propuesta previa para refinar.")

    try:
        settings = get_settings()
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=settings.gemini_api_key,
        )
        prompt = (
            "Refina la siguiente propuesta comercial manteniendo precisión y tono ejecutivo.\n"
            "Aplica estrictamente la instrucción del usuario.\n\n"
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
        return AgentStateResponse(
            thread_id=thread_id,
            empresa=latest.get("empresa", ""),
            area=latest.get("area", ""),
            problema=latest.get("problema", ""),
            casos_encontrados=latest.get("casos_encontrados", []),
            neo_cases=latest.get("neo_cases", []),
            ai_cases=latest.get("ai_cases", []),
            top_match_global=latest.get("top_match_global"),
            top_match_global_reason=latest.get("top_match_global_reason"),
            casos_seleccionados_ids=latest.get("casos_seleccionados_ids", []),
            perfil_cliente=latest.get("perfil_cliente"),
            propuesta_final=latest.get("propuesta_final"),
            status="completed",
            error=latest.get("error"),
        )
    except Exception as exc:
        logger.exception("Error refining proposal: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/agent/{thread_id}/state", response_model=AgentStateResponse)
async def get_agent_state(thread_id: str):
    """Recupera el estado actual de una sesión."""
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    
    if not state.values:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    
    v = state.values
    return AgentStateResponse(
        thread_id=thread_id,
        empresa=v.get("empresa", ""),
        area=v.get("area", ""),
        problema=v.get("problema", ""),
        casos_encontrados=v.get("casos_encontrados", []),
        neo_cases=v.get("neo_cases", []),
        ai_cases=v.get("ai_cases", []),
        top_match_global=v.get("top_match_global"),
        top_match_global_reason=v.get("top_match_global_reason"),
        casos_seleccionados_ids=v.get("casos_seleccionados_ids", []),
        perfil_cliente=v.get("perfil_cliente"),
        propuesta_final=v.get("propuesta_final"),
        status="completed" if v.get("propuesta_final") else "awaiting_selection",
        error=v.get("error")
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
