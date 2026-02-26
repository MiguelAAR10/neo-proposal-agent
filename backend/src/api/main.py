"""
main.py — FastAPI MVP V2 Backend
Refactored to support LangGraph HITL flow, Redis persistence, and Peru profiles.
"""
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Optional, Literal, List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agent.graph import graph
from src.config import get_settings
from src.tools.qdrant_tool import db_connection

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

class SelectRequest(BaseModel):
    case_ids: List[str] = Field(..., min_items=1)

class AgentStateResponse(BaseModel):
    thread_id: str
    empresa: str
    area: str
    problema: str
    casos_encontrados: List[dict]
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
            casos_seleccionados_ids=final_state.get("casos_seleccionados_ids", []),
            perfil_cliente=final_state.get("perfil_cliente"),
            propuesta_final=final_state.get("propuesta_final"),
            status="awaiting_selection",
            error=final_state.get("error")
        )
    except Exception as e:
        logger.exception(f"Error starting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
            casos_seleccionados_ids=final_state.get("casos_seleccionados_ids", []),
            perfil_cliente=final_state.get("perfil_cliente"),
            propuesta_final=final_state.get("propuesta_final"),
            status="completed",
            error=final_state.get("error")
        )
    except Exception as e:
        logger.exception(f"Error in select_cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        casos_seleccionados_ids=v.get("casos_seleccionados_ids", []),
        perfil_cliente=v.get("perfil_cliente"),
        propuesta_final=v.get("propuesta_final"),
        status="completed" if v.get("propuesta_final") else "awaiting_selection",
        error=v.get("error")
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
