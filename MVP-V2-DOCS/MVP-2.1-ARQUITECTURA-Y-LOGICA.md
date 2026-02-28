# MVP 2.1 - ARQUITECTURA Y LOGICA DE DATOS (ESTADO REAL)

Fecha de corte: 2026-02-28
Version objetivo: MVP V2.1 estable
Baseline funcional: `15bfc20b`
Cierre frontend QA: `7344c78c`

## 1) Objetivo operativo

Entregar un flujo E2E estable:
1. Intake.
2. Busqueda semantica con evidencia.
3. Curacion HITL explicita.
4. Generacion anclada en casos seleccionados.
5. Refinamiento iterativo.

## 2) Contrato tecnico vigente

Endpoints activos:
- `GET /health`
- `POST /api/search`
- `POST /api/ingest`
- `GET /ops/metrics`
- `POST /agent/start`
- `POST /agent/{thread_id}/select`
- `POST /agent/{thread_id}/refine`
- `GET /agent/{thread_id}/state`

Regla de capas:
- `/api/search` = primitiva stateless.
- `/agent/*` = orquestacion con estado de sesion.
- Sin HTTP interno entre endpoints del mismo backend.

## 3) Logica de datos

### 3.1 Ingesta
- Fuentes: `ai_cases.csv`, `neo_legacy.csv`.
- Validacion Pydantic (`CaseInput`).
- `point_id` determinista en Qdrant por `case_id`.

### 3.2 Calidad
Required:
- `id`, `tipo`, `titulo`, `problema`, `solucion`, `url_slide`.

Optional:
- `empresa`, `industria`, `area`, `beneficios`, `stack`, `kpi_impacto`.

Calculados:
- `confianza_fuente`, `data_quality_score`, `semantic_quality`, `fecha_ingesta`, `link_status`.

### 3.3 Busqueda
- Embedding Gemini + busqueda vectorial Qdrant.
- Timeouts defensivos y fallback de cache embedding.
- Segmentacion de respuesta: `neo_cases`, `ai_cases`, `top_match_global`.
- Transparencia de score: label + confidence.

## 4) Estado de implementacion

IMPLEMENTADO:
- Curacion NEO/AI en pantalla unica.
- Seleccion explicita de casos.
- `select` genera propuesta.
- `refine` actualiza propuesta en frontend.
- Metricas operativas basicas (`/ops/metrics`).

PARCIAL:
- Persistencia robusta de metricas (hoy in-memory).
- Validacion mas profunda de calidad de fuente por batch.

BACKLOG:
- Dashboard operativo persistente (p95/p99 historico).
- Exportacion con trazabilidad por version a CRM.

## 5) SLA de referencia

Objetivo:
- p50 < 500ms
- p95 < 900ms
- p99 < 1500ms

Desglose esperado:
- Embedding: 200-600ms
- Qdrant: <80ms p95
- Procesamiento backend: <100ms p95

## 6) Riesgos vigentes y mitigacion

1. Riesgo: data incompleta en origen.
- Mitigacion: score de calidad, link status y validacion de ingesta.

2. Riesgo: deriva docs vs codigo.
- Mitigacion: regla P0 (bitacora + req 04/05 en el mismo ciclo).

3. Riesgo: latencia variable de Gemini.
- Mitigacion: timeouts, cache y monitoreo por componente.

