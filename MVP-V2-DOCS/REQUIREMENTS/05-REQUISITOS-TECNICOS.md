# 05 - REQUISITOS TECNICOS (MVP V2)

Fecha de corte: 2026-02-28  
Version objetivo: MVP V2.1 estable

## 1) Stack real (backend)

- Python 3.13
- FastAPI
- LangGraph
- LangChain Google Generative AI
- Qdrant Client
- Redis (sesion/cache)
- Pydantic v2

## 2) Contrato API vigente

Core:
- `POST /api/search`

Orquestacion:
- `POST /agent/start`
- `POST /agent/{thread_id}/select`
- `POST /agent/{thread_id}/refine`
- `GET /agent/{thread_id}/state`

Operaciones:
- `GET /health`
- `GET /ops/metrics`
- `POST /api/ingest`

## 3) Requisitos de arquitectura

1. Dominio separado de API.
2. Reuso de logica de busqueda entre primitiva y orquestador.
3. Estado de sesion por `thread_id`.
4. Redis obligatorio en `staging/prod`; fallback memoria solo local.

## 4) Requisitos de datos

### Required
- `case_id`, `tipo`, `titulo`, `problema`, `solucion`, `url_slide`.

### Optional
- `empresa`, `industria`, `area`, `beneficios`, `stack`, `kpi_impacto`.

### Calculados
- `confianza_fuente`, `data_quality_score`, `semantic_quality`, `fecha_ingesta`.

### Calidad de links
- `link_status` (`verified|inaccessible|unknown`) actualizado por job batch.

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

Parcial:
- falta persistencia historica (APM/metrics backend dedicado).

## 7) Seguridad minima

Implementado:
- CORS por allowlist (`allowed_origins_raw`).
- `ADMIN_TOKEN` obligatorio en `staging/prod` para admin/ops.
- validacion Pydantic en requests.

Backlog:
- rate limiting formal.
- auth por roles para operaciones.

## 8) Criterios tecnicos de merge

Checklist:
1. contrato de endpoint definido y estable.
2. cobertura minima de tests para cambios de dominio.
3. sin regresion del flujo HITL.
4. bitacora actualizada con motivo tecnico + impacto negocio.

## 9) Backlog tecnico V2.2

1. endpoint dedicado de chat contextual con memoria conversacional por `thread_id`.
2. metricas persistentes (Prometheus/Datadog/LangSmith).
3. health checks profundos por dependencia.
4. reporte persistente de calidad de ingesta por categoria.
