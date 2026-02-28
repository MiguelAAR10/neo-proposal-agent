# SKILL_BACKEND_EXPERT - NEO PROPOSAL AGENT

Fecha de corte: 2026-02-28
Estado: ACTIVA

## 1) Cuando activar

Activar para cualquier cambio en:
- `backend/src/*`
- contratos API
- busqueda semantica
- ingesta y calidad de datos
- orquestacion HITL y estado de sesion

## 2) Objetivo del rol

Diseñar e implementar backend con enfoque de Staff Engineer:
1. claridad de arquitectura,
2. correctitud y edge cases primero,
3. performance medible,
4. observabilidad minima,
5. trazabilidad tecnica y de negocio.

## 3) Principios obligatorios

1. DRY pragmatico (sin abstracciones artificiales).
2. Explicito > clever.
3. Tipado y errores de dominio claros.
4. Sin HTTP interno entre endpoints del mismo servicio.
5. Cambios pequeños, testeables y reversibles.

## 4) Contrato tecnico a respetar

Endpoints base:
- `POST /api/search`
- `POST /agent/start`
- `POST /agent/{thread_id}/select`
- `POST /agent/{thread_id}/refine`
- `GET /agent/{thread_id}/state`
- `POST /api/ingest`
- `GET /health`
- `GET /ops/metrics`

Reglas:
- `/api/search` es primitiva stateless.
- `/agent/*` orquesta estado conversacional.
- Reutilizar servicio de dominio compartido.

## 5) Checklist tecnico minimo

Arquitectura:
- limites de modulo claros,
- acoplamiento controlado,
- contrato API estable.

Calidad:
- validacion de input,
- errores tipificados,
- logs con contexto (`thread_id`, latencia, endpoint).

Datos:
- `case_id` determinista,
- required/optional/fallback coherentes,
- calidad y link_status visibles.

Performance:
- timeouts defensivos,
- cache con criterio,
- metricas por componente.

Pruebas:
- unitarias de logica,
- contract tests de endpoints,
- validacion E2E minima.

## 6) Entregable obligatorio por cambio backend

1. Codigo + pruebas.
2. Validacion ejecutada.
3. Bitacora actualizada con:
- objetivo,
- decision,
- tradeoff,
- impacto de negocio,
- estado.

## 7) Anti-patrones prohibidos

- Duplicar logica entre nodos/endpoints.
- Mezclar V1/V2 en contratos.
- Silenciar errores con `except` generico sin contexto.
- Cerrar feature sin test ni evidencia de validacion.

