"""
api.py — FastAPI: /search + /chat endpoints
Run: uvicorn api:app --reload --port 8000
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

load_dotenv()
logger = logging.getLogger("neo_api")

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
    message: str = Field(..., min_length=1, max_length=3000)
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
MAX_CHAT_CASES = 4
MAX_CHAT_HISTORY = 6
MAX_FIELD_CHARS = 500
MAX_MESSAGE_CHARS = 1500


def _truncate(value: object, max_chars: int = MAX_FIELD_CHARS) -> str:
    text = str(value or "").strip()
    return text[:max_chars]


def _normalize_history(raw_history: Optional[list[dict]]) -> list[dict]:
    normalized: list[dict] = []
    if not raw_history:
        return normalized

    for item in raw_history[-MAX_CHAT_HISTORY:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = _truncate(item.get("content"), max_chars=MAX_FIELD_CHARS)
        if role not in {"user", "assistant"} or not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized


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


def _should_retry_genai(exc: Exception) -> bool:
    text = str(exc).upper()
    transient_markers = (
        "429",
        "RESOURCE_EXHAUSTED",
        "RATE LIMIT",
        "DEADLINE",
        "TIMEOUT",
        "UNAVAILABLE",
        "503",
    )
    return any(marker in text for marker in transient_markers)


def _generate_with_retry(prompt: str, retries: int = 2) -> str:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = genai_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            return (response.text or "").strip()
        except Exception as exc:
            last_exc = exc
            if attempt == retries or not _should_retry_genai(exc):
                break
            time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"Error generando respuesta del chat: {last_exc}") from last_exc


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
        user_message = _truncate(request.message, max_chars=MAX_MESSAGE_CHARS)
        if not user_message:
            raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

        safe_cases = _normalize_cases(request.cases_context)
        safe_history = _normalize_history(request.history)

        # Construir contexto de casos
        cases_text = ""
        if safe_cases:
            cases_text = "\n\n**CASOS DE ÉXITO ENCONTRADOS:**\n"
            for i, case in enumerate(safe_cases, 1):
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
        if safe_history:
            history_text = "\n**HISTORIAL DE CONVERSACIÓN:**\n"
            for msg in safe_history:
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

        full_prompt = f"{system_prompt}\n\nConsultor: {user_message}\n\nNEO Assistant:"

        reply = _generate_with_retry(full_prompt)
        if not reply:
            reply = (
                "No pude completar la respuesta en este intento. "
                "Intenta reformular en una pregunta más corta o volver a consultar."
            )
        return ChatResponse(reply=reply)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en /chat")
        return ChatResponse(
            reply=(
                "Tuve un problema temporal procesando el chat. "
                "Puedes reintentar ahora o hacer una pregunta más específica."
            )
        )
