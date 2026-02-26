# SKILL: Backend Expert (FastAPI + LangGraph + Qdrant)

## Perfil del Experto

**Especialización:** Desarrollador senior especializado en:
- Arquitecturas Python async con FastAPI
- Orquestación de agentes con LangGraph
- Sistemas de información retrieval con vector databases
- Integración con LLMs (Gemini)
- Caching distribuido con Redis

**Experiencia requerida:**
- 5+ años con Python
- 3+ años con FastAPI
- 2+ años con LLMs/RAG
- Experiencia con Qdrant o similar
- Conocimiento de arquitecturas escalables

**Responsabilidades:**
- Diseñar e implementar la lógica del agente
- Orquestar flujos complejos con LangGraph
- Optimizar búsquedas en Qdrant
- Implementar caching inteligente
- Asegurar performance y escalabilidad
- Manejar errores y fallbacks gracefully

---

## Stack Obligatorio

```
Backend Framework:
  - FastAPI 0.110+
  - Uvicorn (ASGI server)
  - Pydantic v2 (validación)
  - python-dotenv (config)

Agente & LLM:
  - LangGraph 0.1+
  - LangChain Core
  - LangChain Community
  - google-generativeai (Gemini)
  - Tenacity (retry logic)

Vector Database:
  - qdrant-client
  - numpy

Cache & Session:
  - redis-py
  - aioredis (async)

Utilities:
  - structlog (logging)
  - httpx (async HTTP)
  - python-multipart (forms)

Testing:
  - pytest
  - pytest-asyncio
  - pytest-cov
  - httpx (test client)
```

---

## Estructura de Código Esperada

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, lifespan, middleware
│   ├── config.py               # Pydantic Settings
│   ├── dependencies.py         # Inyección de dependencias
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── agent.py            # Endpoints del agente
│   │   └── admin.py            # Endpoints de administración
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agent_service.py    # Orquestación LangGraph
│   │   ├── qdrant_service.py   # Cliente Qdrant
│   │   ├── redis_service.py    # Cliente Redis
│   │   ├── gemini_service.py   # Cliente Gemini
│   │   └── search_service.py   # Lógica de búsqueda
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── graph.py            # Compilación del grafo
│   │   ├── state.py            # TypedDict del estado
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── intake.py       # Validación de inputs
│   │       ├── search.py       # Búsqueda de casos
│   │       ├── curate.py       # Interrupt node (HITL)
│   │       ├── enrich.py       # Enriquecimiento
│   │       ├── draft.py        # Generación de propuesta
│   │       └── refine.py       # Refinamiento conversacional
│   │
│   └── models/
│       ├── __init__.py
│       ├── requests.py         # Pydantic request schemas
│       └── responses.py        # Pydantic response schemas
│
├── scripts/
│   ├── ingest_cases.py         # CLI para ingestar CSVs
│   ├── recreate_collection.py  # CLI para reset Qdrant
│   └── warm_cache.py           # CLI para precargar cache
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Patrones de Implementación Clave

### 1. Configuración con Pydantic Settings

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_cases: str = "neo_cases_v1"
    qdrant_collection_profiles: str = "neo_profiles_v1"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # FastAPI
    api_title: str = "NEO Proposal Agent"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 2. Inyección de Dependencias

```python
# app/dependencies.py
from fastapi import Depends
from functools import lru_cache
from qdrant_client import QdrantClient
import redis.asyncio as redis

from app.config import get_settings

@lru_cache()
def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url)

@lru_cache()
async def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return await redis.from_url(settings.redis_url)

# Uso en servicios
class QdrantService:
    def __init__(self, client: QdrantClient = Depends(get_qdrant_client)):
        self.client = client
        self.settings = get_settings()
```

### 3. LangGraph con Interrupt y RedisSaver

```python
# app/graph/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import RedisSaver
from app.graph.state import ProposalState
from app.graph.nodes import (
    intake_node, search_node, curate_node,
    enrich_node, draft_node, refine_node
)

def build_graph(redis_client) -> StateGraph:
    builder = StateGraph(ProposalState)
    
    # Agregar nodos
    builder.add_node("intake", intake_node)
    builder.add_node("search", search_node)
    builder.add_node("curate", curate_node)  # HITL
    builder.add_node("enrich", enrich_node)
    builder.add_node("draft", draft_node)
    builder.add_node("refine", refine_node)
    
    # Agregar edges
    builder.set_entry_point("intake")
    builder.add_edge("intake", "search")
    builder.add_edge("search", "curate")
    builder.add_edge("curate", "enrich")
    builder.add_edge("enrich", "draft")
    builder.add_edge("draft", "refine")
    builder.add_edge("refine", END)
    
    # Compilar con checkpointer
    checkpointer = RedisSaver(redis_client)
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["curate"]  # Esperar selección usuario
    )
    
    return graph
```

### 4. Endpoint con Manejo de Estado

```python
# app/routers/agent.py
from fastapi import APIRouter, Depends, HTTPException
from app.models.requests import StartRequest, SelectRequest
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/start")
async def start_agent(
    data: StartRequest,
    service: AgentService = Depends(get_agent_service)
) -> dict:
    """Inicia sesión del agente, retorna thread_id."""
    try:
        thread_id = await service.create_thread(data)
        return {
            "success": True,
            "data": {"thread_id": thread_id, "status": "started"}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{thread_id}/select")
async def select_cases(
    thread_id: str,
    data: SelectRequest,
    service: AgentService = Depends(get_agent_service)
) -> dict:
    """Usuario selecciona casos, continúa grafo."""
    try:
        result = await service.continue_with_selection(thread_id, data.case_ids)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 5. Servicio de Búsqueda con Qdrant

```python
# app/services/search_service.py
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.services.gemini_service import GeminiService

class SearchService:
    def __init__(self, qdrant_client, gemini_service: GeminiService):
        self.qdrant = qdrant_client
        self.gemini = gemini_service
    
    async def search_cases(
        self,
        problema: str,
        switch: str,
        limit: int = 6
    ) -> list[dict]:
        """Busca casos similares por embedding."""
        
        # 1. Generar embedding
        embedding = await self.gemini.embed_text(problema)
        
        # 2. Construir filtro según switch
        filter = self._build_tipo_filter(switch)
        
        # 3. Buscar en Qdrant
        results = self.qdrant.search(
            collection_name="neo_cases_v1",
            query_vector=embedding,
            query_filter=filter,
            limit=limit,
            with_payload=True
        )
        
        # 4. Formatear resultados
        cases = [
            {
                "id": result.id,
                "score": result.score,
                **result.payload
            }
            for result in results
        ]
        
        return cases
    
    def _build_tipo_filter(self, switch: str) -> Filter | None:
        """Construye filtro según switch del usuario."""
        if switch == "neo":
            return Filter(
                must=[FieldCondition(
                    key="tipo",
                    match=MatchValue(value="NEO")
                )]
            )
        elif switch == "ai":
            return Filter(
                must=[FieldCondition(
                    key="tipo",
                    match=MatchValue(value="AI")
                )]
            )
        else:  # "both"
            return None
```

### 6. Servicio de Gemini con Retry

```python
# app/services/gemini_service.py
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio

class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.embedding_model = "models/text-embedding-004"
        self.generation_model = "gemini-1.5-flash"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed_text(self, text: str) -> list[float]:
        """Genera embedding de texto."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: genai.embed_content(
                model=self.embedding_model,
                content=text
            )
        )
        return result["embedding"]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_proposal(self, prompt: str) -> str:
        """Genera propuesta con Gemini."""
        loop = asyncio.get_event_loop()
        model = genai.GenerativeModel(self.generation_model)
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1000,
                }
            )
        )
        return response.text
```

### 7. Servicio de Redis con TTL

```python
# app/services/redis_service.py
import redis.asyncio as redis
import json
from datetime import timedelta

class RedisService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get_sector_intel(self, rubro: str, area: str = "") -> dict | None:
        """Obtiene inteligencia de sector del cache."""
        cache_key = f"sector:{rubro.lower()}:{area.lower() or 'general'}"
        data = await self.redis.get(cache_key)
        return json.loads(data) if data else None
    
    async def set_sector_intel(
        self,
        rubro: str,
        area: str,
        data: dict,
        ttl_days: int = 30
    ) -> None:
        """Guarda inteligencia de sector en cache."""
        cache_key = f"sector:{rubro.lower()}:{area.lower() or 'general'}"
        ttl = timedelta(days=ttl_days)
        await self.redis.setex(
            cache_key,
            ttl,
            json.dumps(data)
        )
    
    async def get_session(self, session_id: str) -> dict | None:
        """Obtiene estado de sesión."""
        data = await self.redis.get(f"session:{session_id}")
        return json.loads(data) if data else None
    
    async def set_session(self, session_id: str, data: dict) -> None:
        """Guarda estado de sesión (24h TTL)."""
        await self.redis.setex(
            f"session:{session_id}",
            timedelta(hours=24),
            json.dumps(data)
        )
```

### 8. Nodo de Búsqueda en LangGraph

```python
# app/graph/nodes/search.py
from app.graph.state import ProposalState
from app.services.search_service import SearchService

async def search_node(
    state: ProposalState,
    search_service: SearchService
) -> ProposalState:
    """Nodo que busca casos similares."""
    
    try:
        # Buscar casos
        cases = await search_service.search_cases(
            problema=state["problema"],
            switch=state["switch"],
            limit=8
        )
        
        # Actualizar estado
        return {
            **state,
            "cases": cases,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error en search_node: {e}")
        return {
            **state,
            "cases": [],
            "error": str(e)
        }
```

---

## Reglas de Oro del Backend

### 1. Nunca Bloquear el Event Loop
```python
# ❌ MAL - Bloquea
def get_embedding(text: str):
    return genai.embed_content(...)

# ✅ BIEN - Async
async def get_embedding(text: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, genai.embed_content, ...)
```

### 2. Validar en el Borde
```python
# ✅ BIEN - Validación con Pydantic
class SearchRequest(BaseModel):
    problema: str = Field(..., min_length=20, max_length=2000)
    switch: Literal["neo", "ai", "both"] = "both"

@router.post("/search")
async def search(data: SearchRequest):
    # data ya está validado
    ...
```

### 3. Manejar Fallos Gracefully
```python
# ✅ BIEN - Fallback
async def get_sector_intel(rubro: str):
    # Intentar cache
    cached = await redis_service.get(f"sector:{rubro}")
    if cached:
        return cached
    
    # Intentar Gemini
    try:
        intel = await gemini_service.generate_sector_intel(rubro)
        await redis_service.set(f"sector:{rubro}", intel, ttl=30*24*3600)
        return intel
    except Exception as e:
        logger.error(f"Error generando sector intel: {e}")
        # Retornar cache viejo o default
        return {"error": "No disponible"}
```

### 4. Logging Estructurado
```python
# ✅ BIEN - JSON logs
import structlog

logger = structlog.get_logger()

logger.info(
    "search_completed",
    thread_id=thread_id,
    cases_found=len(cases),
    latency_ms=elapsed_ms,
    switch=switch
)
```

### 5. Type Hints Everywhere
```python
# ✅ BIEN - Type hints completos
async def search_cases(
    self,
    problema: str,
    switch: Literal["neo", "ai", "both"],
    limit: int = 6
) -> list[dict]:
    ...
```

### 6. No Secrets en Código
```python
# ❌ MAL
api_key = "sk-1234567890"

# ✅ BIEN
api_key = os.getenv("GEMINI_API_KEY")
```

---

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requiere Qdrant/Redis)
pytest tests/integration/ -v --docker

# Coverage
pytest --cov=app --cov-report=html

# Type checking
mypy app/ --strict

# Linting
black app/ --check
```

---

## Documentación API

FastAPI genera automáticamente:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Mantener schemas Pydantic actualizados para documentación clara.

---

## Performance Checklist

- [ ] Todos los I/O son async
- [ ] Caching implementado para datos frecuentes
- [ ] Índices en Qdrant para filtros
- [ ] Retry logic con exponential backoff
- [ ] Timeout en todas las llamadas externas
- [ ] Connection pooling en Redis y Qdrant
- [ ] Logging de latencias
- [ ] Monitoreo de errores
- [ ] Rate limiting implementado
- [ ] Graceful degradation en fallos

---

## Deployment Checklist

- [ ] Variables de entorno configuradas
- [ ] Secrets en AWS Secrets Manager
- [ ] Health checks implementados
- [ ] Logging centralizado
- [ ] Métricas de Prometheus
- [ ] Alertas configuradas
- [ ] Backup de Qdrant
- [ ] Replicación de Redis
- [ ] Load balancer configurado
- [ ] Auto-scaling policies