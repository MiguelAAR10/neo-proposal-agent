# 04 - REQUISITOS FUNCIONALES (MVP V2)

Fecha de corte: 2026-03-02  
Version objetivo: MVP V2.1 estable + pipeline backend formal (7 fases)

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
Estado: `IMPLEMENTADO`
- endpoint dedicado `POST /agent/{thread_id}/chat`.
- mantiene contexto de cliente priorizado, perfil, sector y casos seleccionados/disponibles.
- persiste historial reciente por sesion para continuidad conversacional.
- aplica guardrails de entrada (inyeccion de prompt, solicitud de secretos, intenciones destructivas, longitud maxima).
- genera trazas de auditoria para operaciones (`GET /ops/chat-audit`).
- permite exportacion de trazas (`GET /ops/chat-audit/export`) para analisis operativo.
- expone KPIs de chat/guardrails (`GET /ops/chat-analytics`) para monitoreo continuo.
- expone alertas automáticas (`GET /ops/chat-alerts`) con severidad `ok|warning|critical`.
- cada alerta incluye `playbook_hint`, `priority` y `owner` para respuesta operativa inmediata.
- expone tendencia de alertas por tiempo (`GET /ops/chat-alerts/history`) para analisis evolutivo.

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

## RF-13 Sales Insight Collector (Human-in-the-Loop)
Estado: `IMPLEMENTADO`

Implementado:
- nueva entidad `HumanInsight` para capturar texto libre del equipo de ventas.
- estructuracion asistida por Gemini a JSON array (pain points, decisores, sentimiento).
- persistencia en tabla `intel_human_insights` vinculada a `company_id`.
- endpoint `POST /intel/company/{company_id}/insights`.
- endpoint `GET /intel/company/{company_id}/profile` para lectura de perfil consolidado intel.
- regla de storage MVP: SQLite + SQLAlchemy + patron Repository (sin Postgres/Mongo/Firestore).
- idempotencia basica por hash para evitar duplicados de reunion.
- integracion de insights humanos en nodo `update_summary` para perfil final de empresa.
- validacion estricta de payload (`author`, `text`, sanitizacion y limites de tamaño).
- errores tipados para parseo (`INSIGHT_PARSE_FAILED`).
- `author` obligatorio para trazabilidad del consultor.
- `department` y `sentiment` deducidos por parser Gemini y persistidos por insight.
- resumen `update_summary` incorpora criterio de relevancia temporal (time-decay) y segmentacion por departamentos.

## RF-14 Macro-Intelligence Radar (Agentic Scraping)
Estado: `IMPLEMENTADO`

Implementado:
- workflow LangGraph `macro_radar_graph` con nodos:
  - `collect_signals`
  - `evaluate_triggers`
  - `update_industry_profile`
- tools agentic desacopladas:
  - `search_market_trends` (Tavily/Perplexity + fallback mock)
  - `scrape_regulatory_site` (Firecrawl + fallback mock markdown regulatorio)
  - `get_financial_ticker` (yfinance + fallback mock determinístico)
- endpoint `POST /intel/radar/run` para ejecución sync del radar en MVP.
- extracción de triggers críticos (leyes/circulares, caída de ticker <= -5%, alertas de consultoras top).
- persistencia de radiografía de industria en SQLite (`intel_industry_radiography`) con patrón Repository.

## Referencias
- `backend/src/api/main.py`
- `backend/src/api/intel.py` (target aprobado)
- `backend/src/intel_pipeline/orchestrator/macro_radar_graph.py`
- `backend/src/intel_pipeline/orchestrator/nodes.py`
- `backend/src/intel_pipeline/collectors/agentic_tools.py`
- `backend/src/agent/graph.py`
- `backend/src/agent/nodes.py`
- `backend/src/services/search_service.py`
- `backend/src/services/metrics.py`
- `backend/src/services/human_insight_parser.py`
- `backend/src/services/intel_storage.py`
- `backend/src/repositories/sqlite_repositories.py`
- `backend/src/tools/qdrant_tool.py`
- `backend/src/tools/verify_links_job.py`
