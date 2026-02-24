"""
api.py — FastAPI: /search + /chat endpoints
Run: uvicorn api:app --reload --port 8000
"""
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

load_dotenv()

# --- Config ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = os.getenv("QDRANT_COLLECTION", "neo_casos")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
EMBEDDING_MODEL = "gemini-embedding-001"  # Único modelo disponible

# --- Clients (lazy-init) ---
genai_client: genai.Client | None = None
qdrant: QdrantClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global genai_client, qdrant
    genai_client = genai.Client(api_key=GOOGLE_API_KEY)
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    print(f"✅ Clients ready | model={GEMINI_MODEL} | collection={COLLECTION}")
    yield
    if qdrant:
        qdrant.close()


app = FastAPI(title="NEO Intelligence API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# --- Schemas ---
class SearchRequest(BaseModel):
    query: str
    industria: Optional[str] = None
    area_funcional: Optional[str] = None
    top_k: int = 5


class ChatRequest(BaseModel):
    message: str
    cases_context: Optional[list[dict]] = None  # casos encontrados previamente
    history: Optional[list[dict]] = None  # [{role: user/assistant, content: ...}]


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
def _embed(text: str) -> list[float]:
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
    if not cases:
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
        response = genai_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
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
    return {"status": "running", "service": "NEO Intelligence API", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/search", response_model=list[CaseResult])
def search_cases(request: SearchRequest):
    """Búsqueda semántica sobre la base de casos NEO."""
    try:
        query_vector = _embed(request.query)
        qfilter = _build_filter(request.industria, request.area_funcional)

        search_kwargs = {
            "collection_name": COLLECTION,
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
def chat_with_cases(request: ChatRequest):
    """Chat RAG: el consultor dialoga sobre los casos encontrados."""
    try:
        # Construir contexto de casos
        cases_text = ""
        if request.cases_context:
            cases_text = "\n\n**CASOS DE ÉXITO ENCONTRADOS:**\n"
            for i, case in enumerate(request.cases_context, 1):
                cases_text += f"""
Caso {i}: {case.get('empresa', 'N/A')} ({case.get('industria', 'N/A')} · {case.get('area_funcional', 'N/A')})
- Relevancia: {int(case.get('score', 0) * 100)}%
- Problema: {case.get('problema', 'N/A')}
- Solución aplicada: {case.get('solucion', 'N/A')}
- Resultados obtenidos: {case.get('resultados', 'No documentados')}
- Tecnologías: {', '.join(case.get('tecnologias', [])) or 'No especificadas'}
- Trigger comercial: {case.get('trigger_comercial', 'N/A')}
"""

        # Construir historial
        history_text = ""
        if request.history:
            history_text = "\n**HISTORIAL DE CONVERSACIÓN:**\n"
            for msg in request.history[-6:]:  # Últimos 6 mensajes
                role = "Consultor" if msg["role"] == "user" else "NEO Assistant"
                history_text += f"{role}: {msg['content']}\n"

        system_prompt = f"""Eres NEO Intelligence Assistant, un experto consultor de estrategia digital con acceso a la base de casos de éxito de NEO Consulting.

Tu rol es ayudar al consultor a:
1. Entender en profundidad los casos encontrados
2. Identificar qué elementos de cada caso son más relevantes para su cliente actual
3. Sugerir cómo adaptar las soluciones al contexto específico del cliente
4. Generar ideas de propuesta de valor basadas en los casos
5. Responder preguntas técnicas sobre las soluciones implementadas

{cases_text}
{history_text}

Responde de manera profesional, concisa y orientada a valor comercial. 
Si el consultor menciona el nombre de su cliente o industria, personaliza tu respuesta.
Siempre cita los casos específicos cuando los referencie."""

        full_prompt = f"{system_prompt}\n\nConsultor: {request.message}\n\nNEO Assistant:"

        response = genai_client.models.generate_content(model=GEMINI_MODEL, contents=full_prompt)
        return ChatResponse(reply=response.text.strip())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
