# 02 - ARQUITECTURA DEL SISTEMA (ESTADO REAL + TARGET)

Fecha de corte: 2026-02-28  
Version objetivo: MVP V2.1 estable

## 1) Objetivo arquitectonico

Arquitectura Backend-First para:
- busqueda semantica confiable,
- curacion HITL con seleccion explicita,
- generacion/refinamiento de propuesta con estado por `thread_id`,
- operacion trazable (errores, latencia, calidad de evidencia).

## 2) Componentes (estado real)

```text
Frontend (Next.js)
  -> /agent/start
  -> /agent/{thread_id}/select
  -> /agent/{thread_id}/refine
  -> /agent/{thread_id}/state

Backend (FastAPI + LangGraph)
  - API Primitiva: /api/search
  - Orquestador HITL: /agent/*
  - Admin: /api/ingest
  - Ops: /ops/metrics

Dependencias
  - Qdrant: neo_cases_v1, neo_profiles_v1
  - Redis: sesiones no-local + cache embeddings (fallback local)
  - Gemini: embeddings y generacion
```

## 3) Principios no negociables

1. Single Source of Truth en runtime: Qdrant/Redis (no CSV).
2. Dominio separado de exposicion HTTP.
3. Vector semantico separado de metadata.
4. HITL real: sin seleccion no hay propuesta.
5. Transparencia: score legible + calidad de evidencia.

## 4) Contratos API vigentes (implementado)

- `GET /health`
- `POST /api/search`
- `GET /ops/metrics`
- `POST /api/ingest`
- `POST /agent/start`
- `POST /agent/{thread_id}/select`
- `POST /agent/{thread_id}/refine`
- `GET /agent/{thread_id}/state`

## 5) Estado por capacidad

### Implementado
- busqueda semantica con segmentacion `neo/ai/both`.
- `top_match_global` para transparencia de relevancia.
- orquestacion HITL con `interrupt_before`.
- errores de dominio tipificados en API.
- cache de embeddings en Redis con fallback local.
- metricas SLA in-memory (p50/p95/p99) via `/ops/metrics`.
- job batch de verificacion de links (`link_status`).

### Parcial
- `health` aun no hace verificacion profunda de dependencias (qdrant/redis/gemini real-time).
- metricas SLA no persistentes (se pierden al reinicio).

### Backlog
- chat contextual productivo (frontend hoy mock).
- observabilidad persistente (Prometheus/Datadog/LangSmith).

## 6) Seguridad y entorno

Implementado:
- CORS por allowlist configurable.
- `ADMIN_TOKEN` requerido en `staging/prod` para endpoints admin/ops.
- Redis obligatorio en `staging/prod` para persistencia de sesion.

Backlog:
- rate limiting formal por IP.
- authn/authz por rol para admin/ops.

## 7) SLA operativo objetivo

- p50 < 500ms
- p95 < 900ms
- p99 < 1500ms

Control actual:
- medido en `/ops/metrics` (ventana in-memory).

## 8) Riesgo principal abierto

Sin chat contextual real, el loop de refinamiento en UI no esta completamente cerrado en experiencia conversacional, aunque backend de refine si existe.
