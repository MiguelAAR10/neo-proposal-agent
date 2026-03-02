# 02 - ARQUITECTURA DEL SISTEMA (ESTADO REAL + TARGET)

Fecha de corte: 2026-03-02  
Version objetivo: MVP V2.1 estable + pipeline backend formal (en ejecucion)

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
  -> /agent/{thread_id}/chat
  -> /agent/{thread_id}/state

Backend (FastAPI + LangGraph)
  - API Primitiva: /api/search
  - Orquestador HITL: /agent/*
  - Admin: /api/ingest
  - Ops: /ops/metrics
  - Ops chat audit: /ops/chat-audit
  - Ops chat audit export: /ops/chat-audit/export
  - Ops chat analytics: /ops/chat-analytics
  - Ops chat alerts: /ops/chat-alerts
  - Ops chat alerts history: /ops/chat-alerts/history

Dependencias
  - Qdrant: `neo_cases_v1` (busqueda semantica exclusivamente)
  - SQLite (SQLAlchemy): perfiles e insights humanos relacionales/JSON
  - Redis: sesiones no-local + cache embeddings (fallback local)
  - Gemini: embeddings, generacion y estructuracion de insights humanos
```

## 3) Principios no negociables

1. Source of Truth por dominio:
   - Qdrant para semantica,
   - SQLite para entidades relacionales y perfiles,
   - Redis para sesion/cache operativo.
2. Dominio separado de exposicion HTTP.
3. Vector semantico separado de metadata.
4. HITL real: sin seleccion no hay propuesta.
5. Transparencia: score legible + calidad de evidencia.
6. Patrón Repository obligatorio en storage para migracion futura a Postgres/pgvector sin tocar logica core.
7. Restriccion MVP: no usar Postgres, MongoDB ni Firestore.

## 4) Contratos API (vigentes + aprobados en ejecucion)

Implementado:
- `GET /health`
- `POST /api/search`
- `GET /ops/metrics`
- `GET /ops/chat-audit`
- `GET /ops/chat-audit/export`
- `GET /ops/chat-analytics`
- `GET /ops/chat-alerts`
- `GET /ops/chat-alerts/history`
- `POST /api/ingest`
- `POST /agent/start`
- `POST /agent/{thread_id}/select`
- `POST /agent/{thread_id}/refine`
- `POST /agent/{thread_id}/chat`
- `GET /agent/{thread_id}/state`

Aprobado (Fase 4, en implementacion):
- `POST /intel/company/{company_id}/insights`

## 5) Estado por capacidad

### Implementado
- busqueda semantica con segmentacion `neo/ai/both`.
- `top_match_global` para transparencia de relevancia.
- orquestacion HITL con `interrupt_before`.
- errores de dominio tipificados en API.
- cache de embeddings en Redis con fallback local.
- metricas SLA in-memory (p50/p95/p99) via `/ops/metrics`.
- job batch de verificacion de links (`link_status`).
- auditoria de chat/guardrails con persistencia Redis opcional y fallback memoria via `/ops/chat-audit`.
- export operativo de auditoria (`json/csv`) via `/ops/chat-audit/export`.
- analitica operativa de chat/guardrails via `/ops/chat-analytics`.
- alertas automaticas por umbral/severidad via `/ops/chat-alerts`.
- alertas incluyen playbook accionable por codigo (owner/prioridad/paso sugerido).
- historial temporal de alertas por bucket (`hour/day`) via `/ops/chat-alerts/history`.
- collector HITL de ventas con endpoint `POST /intel/company/{company_id}/insights`.
- repositorios SQLite para insights/perfiles con patron Repository.
- nodo `update_summary` para fusion de contexto sectorial + ultimos insights humanos.
- storage intel en modo SQLAlchemy estricto (sin driver sqlite3 alterno).
- metricas operativas intel agregadas en `/ops/metrics`.

### Parcial
- `health` aun no hace verificacion profunda de dependencias (qdrant/redis/gemini real-time).
- metricas SLA no persistentes (se pierden al reinicio).
- auditoria de chat depende de Redis para persistencia cross-restart; en fallback memoria se pierde al reinicio.

### Backlog
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

Riesgo principal abierto: consolidar observabilidad persistente y cerrar integracion del collector humano sin aumentar acoplamiento entre API, nodos y storage.
