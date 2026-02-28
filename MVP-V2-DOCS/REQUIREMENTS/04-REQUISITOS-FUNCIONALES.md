# 04 - REQUISITOS FUNCIONALES (MVP V2)

Fecha de corte: 2026-02-28  
Version objetivo: MVP V2.1 estable + backlog V2.2

## Convencion de estado

- `IMPLEMENTADO`: funcional en rama actual.
- `PARCIAL`: existe base, falta cierre completo.
- `BACKLOG`: aun no implementado.

## RF-01 Intake inicial con switch de fuentes
Estado: `IMPLEMENTADO`
- captura `empresa`, `rubro`, `area`, `problema`, `switch`.
- switch soporta `neo|ai|both`.
- validaciones minimas activas en request.

## RF-02 Busqueda semantica reutilizable
Estado: `IMPLEMENTADO`
- `POST /api/search` stateless.
- salida con `casos`, `neo_cases`, `ai_cases`, `top_match_global` (si aplica).
- score transparente (`score_raw`, `score_label`, `confidence`).

## RF-03 Flujo HITL start -> select
Estado: `IMPLEMENTADO`
- `POST /agent/start` crea sesion y retorna casos.
- `POST /agent/{thread_id}/select` persiste seleccion y genera propuesta.
- seleccion valida requerida para propuesta.

## RF-04 Segmentacion NEO/AI y evidencia visible
Estado: `IMPLEMENTADO`
- resultados segmentados por tipo.
- `top_match_global` cuando AI supera al mejor NEO.
- cada caso expone evidencia base (problema, solucion, KPI, URL cuando existe).

## RF-05 Generacion de propuesta anclada a seleccion
Estado: `IMPLEMENTADO`
- usa `selected_case_ids` de sesion.
- usa perfil cliente cuando existe.
- persiste propuesta en estado.

## RF-06 Refinamiento de propuesta
Estado: `IMPLEMENTADO`
- `POST /agent/{thread_id}/refine` con `instruction`.
- versionado en `propuesta_versiones`.

## RF-07 Recuperacion de estado de sesion
Estado: `IMPLEMENTADO`
- `GET /agent/{thread_id}/state`.
- estado coherente: `awaiting_selection` o `completed`.

## RF-08 Chat contextual en curacion/refinamiento
Estado: `PARCIAL`
- backend refine existe.
- UI de chat sigue mock en frontend.
- falta endpoint de chat contextual dedicado.

## RF-09 Ingesta administrativa de casos
Estado: `IMPLEMENTADO`
- `POST /api/ingest` con `force_rebuild`.
- validacion de CSVs y upsert en `neo_cases_v1`.

## RF-10 Calidad de datos y evidencia
Estado: `PARCIAL`

Implementado:
- validacion pydantic de casos.
- `data_quality_score` y `semantic_quality`.
- job batch de verificacion de links y actualizacion `link_status`.

Pendiente:
- reporte persistente de rechazos por categoria (dashboard/report formal).

## RF-11 Observabilidad operativa de busqueda
Estado: `IMPLEMENTADO`
- metrica de busqueda por ventana: p50/p95/p99.
- cache hit/miss y errores por categoria.
- endpoint `GET /ops/metrics` para supervision.

## RF-12 Seguridad de endpoints operativos
Estado: `IMPLEMENTADO`
- `ADMIN_TOKEN` obligatorio en `staging/prod` para ops/admin.
- CORS por allowlist configurable.

## Referencias
- `backend/src/api/main.py`
- `backend/src/agent/graph.py`
- `backend/src/agent/nodes.py`
- `backend/src/services/search_service.py`
- `backend/src/services/metrics.py`
- `backend/src/tools/qdrant_tool.py`
- `backend/src/tools/verify_links_job.py`
