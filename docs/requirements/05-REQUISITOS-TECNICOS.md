# 05 - REQUISITOS TÉCNICOS

## RT-01: Backend FastAPI

**Descripción:** API RESTful para orquestar el agente y servir datos al frontend.

**Especificaciones:**
- Framework: FastAPI 0.110+
- Python: 3.11+
- Servidor: Uvicorn con workers configurables
- Documentación automática: OpenAPI/Swagger en `/docs`
- CORS: Configurado para dominios de frontend
- Async: Todas las operaciones I/O deben ser async

**Endpoints Requeridos:**

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/agent/start` | Iniciar sesión con datos iniciales | No |
| POST | `/agent/search` | Buscar casos por problema | No |
| POST | `/agent/{thread_id}/select` | Confirmar casos seleccionados | No |
| POST | `/agent/{thread_id}/generate` | Generar propuesta | No |
| POST | `/agent/{thread_id}/refine` | Refinar propuesta por chat | No |
| GET | `/health` | Health check de servicios | No |
| POST | `/admin/ingest` | Ingestar casos (protegido) | Sí |
| POST | `/admin/cache/invalidate` | Invalidar cache Redis | Sí |
| GET | `/admin/stats` | Estadísticas del sistema | Sí |

**Estructura de Respuesta Estándar:**
```json
{
  "success": true,
  "data": {...},
  "error": null,
  "timestamp": "2026-02-25T10:00:00Z"
}
```

**Prioridad:** 🔴 ALTA

---

## RT-02: LangGraph Agent

**Descripción:** Orquestación de flujo conversacional con memoria.

**Especificaciones:**
- Librería: LangGraph 0.1+
- State: TypedDict serializable (JSON)
- Checkpointer: RedisSaver para persistencia
- Interrupts: Antes de `curate_node` para HITL
- Retry: 3 intentos en fallos de LLM
- Timeout: 30 segundos por nodo

**Nodos del Grafo:**

```
intake_node
    ↓
search_node
    ↓
curate_node (INTERRUPT - esperar selección usuario)
    ↓
enrich_node
    ↓
draft_node
    ↓
refine_node (LOOP - refinamiento conversacional)
    ↓
END
```

**Estado (TypedDict):**
```python
class ProposalState(TypedDict):
    # Entrada
    empresa: str
    rubro: str
    area: str
    problema: str
    switch: Literal["neo", "ai", "both"]
    
    # Búsqueda
    cases: list[dict]
    selected_case_ids: list[str]
    
    # Enriquecimiento
    profile: dict | None
    sector_intel: dict | None
    
    # Generación
    proposal: str
    proposal_version: int
    chat_history: list[dict]
    
    # Metadata
    thread_id: str
    created_at: str
    updated_at: str
```

**Prioridad:** 🔴 ALTA

---

## RT-03: Qdrant Vector Database

**Descripción:** Almacenamiento y búsqueda de vectores para casos y perfiles.

**Especificaciones:**
- Versión: 1.9+
- Modo: Docker local (MVP), Cloud/ECS (prod)
- Colecciones: `neo_cases_v1`, `neo_profiles_v1`
- Dimensión vectores: 768 (`gemini-embedding-001`)
- Distancia: Cosine
- Payload indexing: `tipo`, `empresa`, `area`, `rubro`

**Configuración Colección Cases:**
```python
from qdrant_client.models import VectorParams, Distance

client.create_collection(
    collection_name="neo_cases_v1",
    vectors_config=VectorParams(
        size=768,
        distance=Distance.COSINE
    )
)

# Crear índices de payload
client.create_payload_index(
    collection_name="neo_cases_v1",
    field_name="tipo",
    field_schema="keyword"
)
client.create_payload_index(
    collection_name="neo_cases_v1",
    field_name="industria",
    field_schema="keyword"
)
client.create_payload_index(
    collection_name="neo_cases_v1",
    field_name="area",
    field_schema="keyword"
)
```

**Configuración Colección Profiles:**
```python
client.create_collection(
    collection_name="neo_profiles_v1",
    vectors_config=VectorParams(
        size=768,
        distance=Distance.COSINE
    )
)

client.create_payload_index(
    collection_name="neo_profiles_v1",
    field_name="empresa",
    field_schema="keyword"
)
client.create_payload_index(
    collection_name="neo_profiles_v1",
    field_name="area",
    field_schema="keyword"
)
```

**Prioridad:** 🔴 ALTA

---

## RT-04: Redis Cache

**Descripción:** Cache para inteligencia sectorial y sesiones de agente.

**Especificaciones:**
- Versión: 7+
- Modo: Docker local (MVP), ElastiCache (prod)
- Librería Python: redis-py 5+
- Serialización: JSON para objetos complejos
- TTL: Configurado por tipo de dato

**Configuración:**
```python
import redis
import json

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# Guardar dato con TTL
def cache_set(key: str, value: dict, ttl_seconds: int = 86400):
    redis_client.setex(
        key,
        ttl_seconds,
        json.dumps(value)
    )

# Recuperar dato
def cache_get(key: str) -> dict | None:
    data = redis_client.get(key)
    return json.loads(data) if data else None
```

**Estrategias de Cache:**
- Inteligencia sector: TTL 30 días (2,592,000 segundos)
- Resultados búsqueda: TTL 1 hora (3,600 segundos)
- Sesiones LangGraph: TTL 24 horas (86,400 segundos)
- Warm cache: Precargar rubros más consultados

**Prioridad:** 🟡 MEDIA

---

## RT-05: Integración Gemini

**Descripción:** Embeddings y generación de texto.

**Especificaciones:**
- API: Google Generative AI (google-generativeai)
- Modelo embeddings: gemini-embedding-001 (768d)
- Modelo generación: gemini-1.5-flash (default), gemini-1.5-pro (fallback)
- Rate limiting: 60 RPM (Flash), manejar 429 con retry exponencial
- Temperature: 0.3 para propuestas (determinista), 0.7 para chat (creativo)
- Timeout: 30 segundos

**Configuración:**
```python
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

genai.configure(api_key=settings.gemini_api_key)

# Embeddings
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def get_embedding(text: str) -> list[float]:
    result = await genai.embed_content(
        model="models/gemini-embedding-001",
        content=text
    )
    return result["embedding"]

# Generación
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def generate_proposal(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = await model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 1000,
        }
    )
    return response.text
```

**Manejo de Errores:**
- 429 (Rate limit): Retry con exponential backoff
- 500 (Server error): Retry hasta 3 veces
- Timeout: Usar fallback o cache viejo

**Prioridad:** 🔴 ALTA

---

## RT-06: Frontend Next.js

**Descripción:** Interfaz de usuario moderna y responsive.

**Especificaciones:**
- Framework: Next.js 14 (App Router)
- React: 18+
- TypeScript: Strict mode
- Estilos: Tailwind CSS 3.4+
- Componentes: Shadcn/ui o similar
- Estado global: Zustand
- Fetching: TanStack Query (React Query)
- Animaciones: Framer Motion

**Rutas:**
```
/                    - Pantalla inicial (formulario)
/search              - Resultados de casos (tarjetas + chat)
/proposal            - Propuesta generada
/admin               - Panel de administración (protegido)
/admin/ingest        - Ingesta de casos
/admin/stats         - Estadísticas
```

**Estructura de Carpetas:**
```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── search/page.tsx
│   ├── proposal/page.tsx
│   └── admin/
├── components/
│   ├── ui/
│   ├── forms/
│   ├── cards/
│   ├── chat/
│   └── proposal/
├── hooks/
├── stores/
├── types/
├── lib/
└── public/
```

**Prioridad:** 🔴 ALTA

---

## RT-07: Docker y Orquestación

**Descripción:** Contenerización para desarrollo y despliegue.

**Especificaciones:**
- Backend: Dockerfile multi-stage (Python slim)
- Frontend: Dockerfile con Node 20
- Servicios: docker-compose.yml con Qdrant, Redis, Backend
- Health checks: En todos los contenedores

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.9.0
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      qdrant:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000

volumes:
  qdrant_storage:
```

**Prioridad:** 🟡 MEDIA

---

## RT-08: Observabilidad

**Descripción:** Monitoreo y debugging del sistema.

**Especificaciones:**
- Logging: structlog con formato JSON
- Métricas: Prometheus (opcional MVP)
- Tracing: LangSmith para trazas de agente
- Alertas: Log aggregation básico

**Configuración Logging:**
```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

**Variables de Entorno:**
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=xxx
LANGCHAIN_PROJECT=neo-proposal-agent
```

**Prioridad:** 🟢 BAJA (MVP)

---

## RT-09: Seguridad

**Descripción:** Protección básica de datos y acceso.

**Especificaciones:**
- API Keys: Header `X-API-Key` para endpoints admin
- CORS: Orígenes explícitos, no wildcard en prod
- Rate limiting: 100 req/min por IP (middleware)
- Sanitización: Validar inputs con Pydantic
- Secrets: No hardcodear, usar .env + Docker secrets
- HTTPS: Obligatorio en producción

**Implementación CORS:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # ["http://localhost:3000", "https://app.neo.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Implementación Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/agent/search")
@limiter.limit("10/minute")
async def search_cases(request: Request, data: SearchRequest):
    ...
```

**Prioridad:** 🟡 MEDIA

---

## RT-10: Escalabilidad Horizontal

**Descripción:** Preparar arquitectura para crecer sin rewrite.

**Decisiones de Diseño:**
- Stateless backend: Todo en Redis/Qdrant, nada en memoria
- Async endpoints: Usar background tasks para ingestas largas
- Cola de tareas: Celery + Redis (futuro) para jobs pesados
- Read replicas: Qdrant permite replicas de colección
- Load balancing: ALB en AWS para distribuir tráfico

**Patrón Stateless:**
```python
# ❌ MAL - Estado en memoria
class SearchService:
    def __init__(self):
        self.cache = {}  # Perdido si se reinicia

# ✅ BIEN - Estado en Redis
class SearchService:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def cache_result(self, key: str, value: dict):
        await self.redis.setex(key, 3600, json.dumps(value))
```

**Prioridad:** 🟡 MEDIA

---

## RT-11: Testing

**Descripción:** Asegurar calidad del código.

**Especificaciones:**
- Unit tests: pytest para backend, Jest para frontend
- Integration tests: Con Qdrant y Redis en Docker
- E2E tests: Playwright para flujos completos
- Coverage: Mínimo 80%

**Estructura de Tests:**
```
backend/tests/
├── unit/
│   ├── test_embeddings.py
│   ├── test_qdrant_service.py
│   └── test_redis_service.py
├── integration/
│   ├── test_agent_flow.py
│   └── test_api_endpoints.py
└── conftest.py

frontend/tests/
├── unit/
│   ├── components/
│   └── hooks/
├── e2e/
│   └── flows.spec.ts
└── setup.ts
```

**Prioridad:** 🟡 MEDIA

---

## RT-12: CI/CD

**Descripción:** Automatización de build, test y deploy.

**Especificaciones:**
- VCS: GitHub
- CI: GitHub Actions
- Linting: Black (Python), ESLint (JS)
- Type checking: MyPy (Python), TypeScript (JS)
- Testing: Pytest, Jest, Playwright
- Deploy: Manual a staging, automático a prod si tests pasan

**Workflow GitHub Actions:**
```yaml
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      qdrant:
        image: qdrant/qdrant:v1.9.0
      redis:
        image: redis:7-alpine
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Lint
        run: black --check . && mypy .
      
      - name: Test
        run: pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

**Prioridad:** 🟡 MEDIA

---

## Matriz de Tecnologías

| Componente | Tecnología | Versión | Justificación |
|-----------|-----------|---------|---------------|
| Backend | FastAPI | 0.110+ | Async, validación, OpenAPI |
| Agente | LangGraph | 0.1+ | Ciclos, memoria, HITL |
| Vector DB | Qdrant | 1.9+ | Self-hostable, filtrado |
| Cache | Redis | 7+ | Performance, sesiones |
| LLM | Gemini 1.5 | Latest | Embeddings, costo-efectivo |
| Frontend | Next.js | 14+ | SSR, SEO, componentes |
| UI | Tailwind | 3.4+ | Estilos rápidos |
| Estado | Zustand | Latest | Ligero, TypeScript |
| Fetching | TanStack Query | 5+ | Caching, sincronización |
| Animaciones | Framer Motion | Latest | Transiciones suaves |
| Testing | Pytest/Jest | Latest | Cobertura, velocidad |
| Deploy | Docker | Latest | Contenerización |

---

## Dependencias Críticas

```
FastAPI
├── Pydantic v2
├── Uvicorn
└── python-dotenv

LangGraph
├── LangChain Core
├── LangChain Community
└── Tenacity (retry)

Qdrant
├── qdrant-client
└── numpy

Redis
├── redis-py
└── json

Gemini
├── google-generativeai
└── aiohttp

Frontend
├── React 18
├── Next.js 14
├── Tailwind CSS
├── Zustand
├── TanStack Query
└── Framer Motion
```

---

## Checklist de Implementación Técnica

- [ ] Configurar FastAPI con lifespan
- [ ] Implementar LangGraph con RedisSaver
- [ ] Crear colecciones en Qdrant
- [ ] Configurar Redis con TTL
- [ ] Integrar Gemini con retry
- [ ] Setup Next.js con App Router
- [ ] Configurar Zustand store
- [ ] Implementar TanStack Query
- [ ] Setup Docker Compose
- [ ] Configurar GitHub Actions
- [ ] Implementar logging estructurado
- [ ] Agregar rate limiting
- [ ] Configurar CORS
- [ ] Escribir tests unitarios
- [ ] Escribir tests de integración
- [ ] Documentar API con OpenAPI
