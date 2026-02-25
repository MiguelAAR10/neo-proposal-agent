"""
main.py — FastAPI V2 Backend Entrypoint
Run: cd backend && uvicorn src.api.main:app --reload --port 8000
"""
import os
import time
import logging
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from langchain_core.messages import HumanMessage, AIMessage
from src.agent.chat_graph import chat_graph
from src.config import get_settings
from src.agent.graph import graph

load_dotenv()
logger = logging.getLogger("neo_api")

# --- Config ---
settings = get_settings()
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "neo_casos")
EMBEDDING_MODEL = "gemini-embedding-001"  # Único modelo disponible

# --- Clients (lazy-init) ---
genai_client: genai.Client | None = None
qdrant: QdrantClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global genai_client, qdrant
    if settings.gemini_api_key:
        genai_client = genai.Client(api_key=settings.gemini_api_key)
    
    if settings.qdrant_url and settings.qdrant_api_key:
        qdrant = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        print(f"✅ Clients ready | collection={QDRANT_COLLECTION}")
    yield
    if qdrant:
        qdrant.close()


app = FastAPI(title="NEO Intelligence API V2", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# --- Schemas ---
class SearchRequest(BaseModel):
    query: str
    industria: Optional[str] = None
    area_funcional: Optional[str] = None
    top_k: int = 5


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=3000)
    cases_context: Optional[list[dict]] = None
    history: Optional[list[dict]] = None  # [{role: user/assistant, content: ...}]
    session_id: str = "default_session"


class CaseResult(BaseModel):
    id_caso: str
    titulo: str
    empresa: str
    industria: str
    subindustria: Optional[str] = None
    area_funcional: str
    problema: str
    trigger_comercial: Optional[str] = None
    solucion: str
    resultados: Optional[str] = None
    tecnologias: list[str]
    url_slide: Optional[str] = None
    score: float
    relevancia: str


class ChatResponse(BaseModel):
    reply: str


# --- Helpers ---
MAX_CHAT_CASES = 4
MAX_FIELD_CHARS = 500

def _truncate(value: object, max_chars: int = MAX_FIELD_CHARS) -> str:
    text = str(value or "").strip()
    return text[:max_chars]

def _normalize_cases(raw_cases: Optional[list[dict]]) -> list[dict]:
    normalized: list[dict] = []
    if not raw_cases:
        return normalized

    for case in raw_cases[:MAX_CHAT_CASES]:
        if not isinstance(case, dict):
            continue
        techs = case.get("tecnologias") or []
        if not isinstance(techs, list):
            techs = []
        try:
            score = float(case.get("score", 0) or 0)
        except (TypeError, ValueError):
            score = 0.0
        normalized.append(
            {
                "empresa": _truncate(case.get("empresa", "N/A"), max_chars=80),
                "industria": _truncate(case.get("industria", "N/A"), max_chars=80),
                "area_funcional": _truncate(case.get("area_funcional", "N/A"), max_chars=80),
                "score": score,
                "problema": _truncate(case.get("problema", "N/A")),
                "solucion": _truncate(case.get("solucion", "N/A")),
                "resultados": _truncate(case.get("resultados", "No documentados")),
                "tecnologias": [str(t).strip()[:40] for t in techs[:8] if str(t).strip()],
                "trigger_comercial": _truncate(case.get("trigger_comercial", "N/A"), max_chars=120),
            }
        )
    return normalized

def _embed(text: str) -> list[float]:
    if not genai_client:
        raise RuntimeError("genai_client not initialized")
    result = genai_client.models.embed_content(model=EMBEDDING_MODEL, contents=[text])
    return result.embeddings[0].values

def _build_filter(industria: str | None, area_funcional: str | None) -> Filter | None:
    conditions = []
    if industria:
        conditions.append(FieldCondition(key="industria", match=MatchValue(value=industria)))
    if area_funcional:
        conditions.append(FieldCondition(key="area_funcional", match=MatchValue(value=area_funcional)))
    return Filter(must=conditions) if conditions else None

def _parse_techs(raw) -> list[str]:
    if not raw or (isinstance(raw, float)):
        return []
    if isinstance(raw, list):
        return raw
    return [t.strip() for t in str(raw).split(",") if t.strip()]

def _generate_relevance(query: str, cases: list[dict]) -> list[str]:
    if not cases or not genai_client:
        return []
    top_n = min(3, len(cases))
    lines = []
    for i in range(top_n):
        c = cases[i]
        title = c.get("empresa_nombre", c.get("titulo_corto", "N/A"))
        problem = str(c.get("problema_descripcion", "N/A"))[:120]
        lines.append(f'{i+1}. "{title}" — {problem}')

    prompt = f"""Un consultor busca: "{query}"

Se encontraron estos casos:
{chr(10).join(lines)}

Para cada caso, escribe UNA frase de máximo 15 palabras explicando por qué es relevante para la búsqueda.
Responde SOLO con el formato:
1. [frase]
2. [frase]
3. [frase]

Sin introducción ni explicación adicional."""

    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        response = genai_client.models.generate_content(model=model_name, contents=prompt)
        explanations = []
        for line in response.text.strip().split("\n"):
            line = line.strip()
            if line and line[0].isdigit() and "." in line:
                explanations.append(line.split(".", 1)[1].strip())
        return explanations
    except Exception as e:
        print(f"⚠️ Relevance generation failed: {e}")
        return []


# --- Endpoints ---
@app.get("/")
def root():
    return {"status": "running", "service": "NEO Intelligence API V2"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/config")
def config_status() -> dict[str, bool]:
    s = get_settings()
    return {
        "qdrant_url_configured": bool(s.qdrant_url),
        "qdrant_api_key_configured": bool(s.qdrant_api_key),
        "gemini_api_key_configured": bool(s.gemini_api_key),
    }

@app.post("/agent/run")
def legacy_agent_run(payload: dict[str, str]) -> dict[str, str]:
    """Legacy V1 LangGraph Entrypoint"""
    return {"answer": "Legacy endpoint not supported in V2."}

@app.post("/search", response_model=list[CaseResult])
def search_cases(request: SearchRequest):
    """Búsqueda semántica sobre la base de casos NEO."""
    if not qdrant:
        raise HTTPException(status_code=503, detail="Qdrant no configurado correctamente.")
        
    try:
        query_vector = _embed(request.query)
        qfilter = _build_filter(request.industria, request.area_funcional)

        search_kwargs = {
            "collection_name": QDRANT_COLLECTION,
            "query_vector": query_vector,
            "limit": request.top_k,
            "with_payload": True,
        }
        if qfilter:
            search_kwargs["query_filter"] = qfilter

        hits = qdrant.search(**search_kwargs)
        if not hits:
            return []

        payloads = [hit.payload for hit in hits]
        explanations = _generate_relevance(request.query, payloads)

        results = []
        for i, hit in enumerate(hits):
            p = hit.payload
            results.append(
                CaseResult(
                    id_caso=str(p.get("id", f"CASE-{i}")),
                    titulo=p.get("titulo_corto", p.get("empresa_nombre", "Sin título")),
                    empresa=p.get("empresa_nombre", "N/A"),
                    industria=p.get("industria", "N/A"),
                    subindustria=p.get("subindustria"),
                    area_funcional=p.get("area_funcional", "N/A"),
                    problema=p.get("problema_descripcion", "N/A"),
                    trigger_comercial=p.get("trigger_comercial") or None,
                    solucion=p.get("solucion_descripcion", "N/A"),
                    resultados=p.get("resultados_kpis") or None,
                    tecnologias=_parse_techs(p.get("tecnologias")),
                    url_slide=p.get("fuente_url") or None,
                    score=round(hit.score, 4),
                    relevancia=explanations[i] if i < len(explanations) else "Caso relacionado por similitud semántica",
                )
            )
        return results

    except Exception as e:
        logger.exception("Error en /search")
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@app.post("/chat", response_model=ChatResponse)
def chat_with_cases(request: ChatRequest):
    """Chat RAG: usa LangGraph para memoria y razonamiento."""
    try:
        user_message = _truncate(request.message, max_chars=1500)
        if not user_message:
            raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

        safe_cases = _normalize_cases(request.cases_context)
        
        # Construir contexto de casos
        cases_text = ""
        if safe_cases:
            cases_text = "\n\n**CASOS DE ÉXITO ENCONTRADOS:**\n"
            for i, case in enumerate(safe_cases, 1):
                cases_text += f"""
Caso {i}: {case.get('empresa', 'N/A')} ({case.get('industria', 'N/A')} · {case.get('area_funcional', 'N/A')})
- Problema: {case.get('problema', 'N/A')}
- Solución aplicada: {case.get('solucion', 'N/A')}
- Resultados: {case.get('resultados', 'No documentados')}
"""

        # Pre-populate history if graph state is empty
        # In a real environment, memory keeps it. But to be safe with UI's manual history passing:
        config = {"configurable": {"thread_id": request.session_id}}
        
        # Get current state from LangGraph
        current_state = chat_graph.get_state(config)
        messages_to_add = [HumanMessage(content=user_message)]
        
        # If no state exists but frontend sent history, seed it.
        if not current_state.values.get("messages") and request.history:
            seed_msgs = []
            for m in request.history:
                if m.get("role") == "user":
                    seed_msgs.append(HumanMessage(content=m["content"]))
                else:
                    seed_msgs.append(AIMessage(content=m["content"]))
            messages_to_add = seed_msgs + messages_to_add

        # Run the agent
        response = chat_graph.invoke(
            {
                "messages": messages_to_add,
                "cases_context": cases_text
            }, 
            config=config
        )
        
        # The last message is the AI response
        last_message = response["messages"][-1].content
        return ChatResponse(reply=last_message)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en /chat")
        raise HTTPException(status_code=500, detail=str(e))
