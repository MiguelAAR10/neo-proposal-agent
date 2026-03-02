# 05 - REQUISITOS TECNICOS (MVP V2)

Fecha de corte: 2026-03-02  
Version objetivo: MVP V2.1 estable + pipeline backend formal

## 1) Stack real (backend)

- Python 3.13
- FastAPI
- LangGraph
- LangChain Google Generative AI
- SQLAlchemy + SQLite
- Qdrant Client
- Redis (sesion/cache)
- Pydantic v2

## 2) Contrato API vigente

Core:
- `POST /api/search`
- `POST /intel/company/{company_id}/insights` (aprobado, en implementacion)

Orquestacion:
- `POST /agent/start`
- `POST /agent/{thread_id}/select`
- `POST /agent/{thread_id}/refine`
- `POST /agent/{thread_id}/chat`
- `GET /agent/{thread_id}/state`

Operaciones:
- `GET /health`
- `GET /ops/metrics`
- `GET /ops/chat-audit`
- `GET /ops/chat-audit/export`
- `GET /ops/chat-analytics`
- `GET /ops/chat-alerts`
- `GET /ops/chat-alerts/history`
- `POST /api/ingest`

## 3) Requisitos de arquitectura

1. Dominio separado de API.
2. Reuso de logica de busqueda entre primitiva y orquestador.
3. Estado de sesion por `thread_id`.
4. Redis obligatorio en `staging/prod`; fallback memoria solo local.
5. Patron Repository obligatorio para capa de storage.
6. Restriccion MVP: no Postgres, MongoDB ni Firestore.

## 4) Requisitos de datos

### Required
- `case_id`, `tipo`, `titulo`, `problema`, `solucion`, `url_slide`.

### Optional
- `empresa`, `industria`, `area`, `beneficios`, `stack`, `kpi_impacto`.

### Calculados
- `confianza_fuente`, `data_quality_score`, `semantic_quality`, `fecha_ingesta`.

### Calidad de links
- `link_status` (`verified|inaccessible|unknown`) actualizado por job batch.

### Human insights (nuevo)
- tabla SQLite: `intel_human_insights`.
- campos minimos: `id`, `company_id`, `seller_id`, `raw_text`, `structured_payload(JSON)`, `created_at`.
- `structured_payload` debe contener array con categorias minimas:
  - `pain_points`
  - `decision_makers`
  - `sentiment`

## 5) Requisitos de busqueda y SLA

Implementado:
- timeout embedding: 2s.
- timeout qdrant: 1s.
- threshold configurable (default 0.50).
- cache de embeddings Redis con fallback local.
- normalizacion de query para hit-rate.

Objetivos SLA:
- p50 < 500ms
- p95 < 900ms
- p99 < 1500ms

## 6) Requisitos de observabilidad

Implementado:
- metricas in-memory de busqueda:
  - `latency_ms` p50/p95/p99
  - `embedding_ms`, `qdrant_ms`
  - `cache_hit_rate`
  - errores por categoria
- exposicion via `GET /ops/metrics`.
- metricas in-memory intel:
  - `parse_ms` (avg/max/count)
  - `store_ms` (avg/max/count)
  - `errors_by_code` (incluye `INSIGHT_PARSE_FAILED`)
- auditoria in-memory de chat:
  - persistencia Redis opcional + fallback memoria
  - status (`ok|guardrail_blocked`)
  - `guardrail_code`
  - `used_case_ids`/`used_case_count`
  - `message_preview` (sin texto completo)
  - exposicion via `GET /ops/chat-audit`.
  - exportacion `json/csv` via `GET /ops/chat-audit/export`.
  - KPIs via `GET /ops/chat-analytics`:
    - `guardrail_block_rate`
    - `top_guardrail_codes`
    - `top_case_ids`
    - `top_threads`
    - `top_companies`
  - alertas por umbral via `GET /ops/chat-alerts`:
    - severidad agregada `ok|warning|critical`
    - codigos de alerta (`HIGH_GUARDRAIL_BLOCK_RATE`, `LOW_CASE_GROUNDING`, etc.)
    - control de muestra minima antes de alertado estricto.
    - playbook operativo embebido (`playbook_hint`, `priority`, `owner`) por tipo de alerta.
  - historial de alertas via `GET /ops/chat-alerts/history`:
    - agregacion por `hour|day`
    - series de severidad y codigos por bucket.

Parcial:
- falta observabilidad persistente unificada de SLA + chat en backend dedicado (APM/metrics).

## 7) Seguridad minima

Implementado:
- CORS por allowlist (`allowed_origins_raw`).
- `ADMIN_TOKEN` obligatorio en `staging/prod` para admin/ops.
- validacion Pydantic en requests.
- guardrails conversacionales base en `/agent/{thread_id}/chat` (policy de entrada + codigo de bloqueo + auditoria de timestamp).

Backlog:
- rate limiting formal.
- auth por roles para operaciones.

## 8) Criterios tecnicos de merge

Checklist:
1. contrato de endpoint definido y estable.
2. cobertura minima de tests para cambios de dominio.
3. sin regresion del flujo HITL.
4. bitacora actualizada con motivo tecnico + impacto negocio.
5. no romper contratos existentes de `/agent/*` ni `/api/search`.

## 9) Backlog tecnico V2.2

1. metricas persistentes (Prometheus/Datadog/LangSmith).
2. health checks profundos por dependencia.
3. reporte persistente de calidad de ingesta por categoria.
4. guardrails avanzados conversacionales (clasificacion semantica + auditoria persistente + alertas).
5. migracion controlada de SQLite Repository a Postgres/pgvector (sin refactor de dominio).
