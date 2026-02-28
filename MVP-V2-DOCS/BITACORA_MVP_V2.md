# BITACORA MVP V2 - ESTADO REAL, ERRORES Y TRAZABILIDAD

Fecha de corte: 2026-02-28  
Version objetivo activa: `MVP V2.1 (estable)`  
Commit baseline operativo: `15bfc20b`

## 1) Proposito

Esta bitacora es la referencia operativa de V2.  
Cada entrada conecta: objetivo de version, cambio tecnico, error cometido y aprendizaje.

No reemplaza commits; los vuelve auditables.

## 2) Estado real actual (rama vigente)

Implementado:
- Backend FastAPI con endpoints V2 productivos.
- Primitiva de busqueda `/api/search` con SLA defensivo.
- Orquestacion HITL `/agent/start -> /agent/{thread_id}/select`.
- Refinamiento `/agent/{thread_id}/refine` con versionado en estado.
- Frontend Next.js en pantalla unica con seleccion de casos y propuesta.
- Segmentacion visual NEO/AI y `top_match_global`.

En progreso / pendiente:
- Chat de frontend aun mock (`ChatPanel.tsx`), no conectado a endpoint real.
- Falta tablero de metricas p95/p99 persistente.
- Falta pipeline de validacion asincronica de links (`link_status`) fuera de ingesta.

## 3) Matriz de trazabilidad por commit (V2 reciente)

| Commit | Tipo | Objetivo declarado | Error detectado posteriormente | Aprendizaje tecnico | Estado |
|---|---|---|---|---|---|
| `15bfc20b` | feat(ui) | Mostrar busqueda segmentada por evidencia en una pantalla | Chat panel continuo mock y no conectado | No cerrar UI sin endpoint real del chat | Vigente |
| `f4e86857` | docs | Publicar arquitectura/ejecucion de MVP2.1 | Varias secciones quedaron mas aspiracionales que ejecutables | Documentar siempre con "estado real" + "estado objetivo" separados | Parcial |
| `9944520d` | feat | Primitiva `/api/search`, SLA, ingesta determinista y refine | Reglas de required/optional no quedaron igual de claras en todos los docs | Definir contrato de datos unico y repetirlo en requirements+skills | Vigente |
| `7f983784` | docs | Sincronizar docs V2 con stack actual | Persistio mezcla de naming y rutas antiguas | El index debe apuntar archivos reales del repo, no nombres ideales | Corregido |
| `22cb46a3` | docs(runtime) | Alinear arranque V2 FastAPI+Next.js | Aun existia ruido de V1/Streamlit en otras piezas | Marcar legacy explicitamente y evitar dualidad de ruta oficial | Corregido |
| `19c4facc` | feat | Migracion fuerte a Next.js + refactor backend | Cambios grandes sin trazabilidad granular de riesgos por modulo | Para refactors grandes: dividir en fases con check de regresion | Vigente con deuda |
| `6fe6b081` | feat | Base estable V2 (Redis/profiles/switch/seeding) | Se asumio persistencia sin validar todos los escenarios de falla | Definir fallback formal MemorySaver vs Redis y documentarlo | Vigente |
| `64346670` | chore | Checkpoint base V2 | Checkpoint sin contrato funcional explicito | Todo checkpoint debe incluir criterios de salida verificables | Historico |

Nota: los "errores detectados" son post-mortem tecnico (no juicio personal), para prevenir repeticion.

## 4) Errores sistemicos repetidos y accion correctiva

1. Error: documentacion adelantada al codigo.
- Accion: toda spec debe tener columna de estado (`implementado/en progreso/backlog`).

2. Error: contratos mezclados entre V1/V2.
- Accion: declarar API oficial V2 y marcar V1 como legacy no soportado.

3. Error: commit sin razonamiento arquitectonico.
- Accion: mensaje + bitacora con problema, decision, tradeoff, riesgo.

4. Error: UX avanzada con backend incompleto (chat mock).
- Accion: no considerar feature cerrada hasta conectar extremo a extremo.

## 5) Regla obligatoria para cada commit de V2

Cada commit que cambie comportamiento debe registrar una entrada en bitacora con:
1. Objetivo de negocio/tactico.
2. Cambio tecnico exacto.
3. Riesgo principal.
4. Error introducido o evitado.
5. Criterio de validacion.
6. Estado (`implementado`, `parcial`, `revertido`).

Plantilla sugerida:

```text
[YYYY-MM-DD] tipo(scope): resumen
- objetivo:
- cambio:
- tradeoff:
- error detectado/evitado:
- validacion:
- estado:
```

## 6) Mapa de versiones y objetivo

- `MVP V2.1 (actual)`: busqueda + curation + propuesta en una sola pantalla con segmentacion NEO/AI.
- `MVP V2.2 (objetivo siguiente)`: chat contextual real, telemetria SLA y calidad de datos operativa.

## 7) Definicion de terminado por version

V2.1 se considera estable cuando:
- `/agent/start`, `/agent/select`, `/agent/refine`, `/agent/state` funcionan E2E.
- Seleccion de casos impacta realmente la propuesta.
- Propuesta incluye evidencia (casos + KPI + URL cuando exista).

V2.2 se considera cerrada cuando:
- Chat deja de ser mock y usa contexto de thread real.
- Se exponen metricas p50/p95/p99 en tablero o logs estructurados persistentes.
- Existe job de verificacion de links y se actualiza `link_status`.

## 8) Registro de actualizaciones de esta bitacora

- 2026-02-28: se agrega matriz de trazabilidad por commit y registro explicito de errores/aprendizajes para control de versiones V2.
- 2026-02-28: backend plan fase inicial ejecutada.
  - objetivo: reducir deriva entre `/api/search` y flujo `/agent/*`, y eliminar duplicacion de mapeo de estado.
  - cambio:
    - `search_cases_sync` ahora usa el mismo camino semantico (embed + search_by_vector) que el flujo con SLA.
    - se introdujo mapper unico `_map_state_response` en API para `start/select/refine/state`.
    - se introdujeron errores de dominio tipificados (`ExternalDependencyTimeout`, `SessionNotFoundError`, `BusinessRuleError`).
    - se agregaron tests unitarios en `backend/tests/`.
  - tradeoff:
    - se mantiene fallback en memoria para entorno local, evitando forzar redis en desarrollo.
    - se tipifica timeout externo sin reestructurar aun toda la jerarquia de errores del proyecto.
  - error detectado y corregido:
    - tests iniciales fallaron por import path (`ModuleNotFoundError: src`); se corrigio agregando `backend/` al `sys.path` en tests.
  - validacion:
    - `python -m unittest discover -s backend/tests -p 'test_*.py'` => OK (4 tests).
- 2026-02-28: backend plan fase 2 (robustez operativa y seguridad base) ejecutada.
  - objetivo tecnico:
    - endurecer despliegue por entorno para evitar sesiones perdidas y operacion admin insegura.
  - cambio:
    - `Settings` ahora incluye `app_env`, `allowed_origins_raw`, `allowed_origins` e `is_non_local_env`.
    - CORS pasa de wildcard a allowlist configurable.
    - Redis queda obligatorio en `staging/prod` (fail-fast en graph si no esta disponible).
    - `/api/ingest` exige `ADMIN_TOKEN` en `staging/prod`; en local mantiene flexibilidad.
    - health expone `environment` y `redis_required`.
  - por que negocio (breve):
    - si se pierde estado de sesion en una licitacion, el consultor pierde seleccion/propuesta y retrabaja.
    - si ingest admin queda abierto en produccion, puede contaminar evidencia y bajar calidad comercial.
    - estos controles mejoran continuidad operativa y confianza en la propuesta generada.
  - tradeoff:
    - mas estrictos en no-local (puede fallar arranque si Redis/token no estan bien configurados).
    - se acepta para evitar riesgos silenciosos en produccion.
  - validacion:
    - `python -m unittest discover -s backend/tests -p 'test_*.py'` => OK (6 tests).
- 2026-02-28: backend plan fase 3A (performance de busqueda) ejecutada.
  - objetivo tecnico:
    - mejorar latencia y estabilidad de embeddings en escenarios de alta repeticion de consultas.
  - cambio:
    - cache de embeddings evoluciona a Redis (si disponible) con fallback local en memoria.
    - normalizacion de query para mejorar hit-rate (`"Mejorar   scoring"` == `"mejorar scoring"`).
  - por que negocio (breve):
    - reduce tiempos de respuesta en busquedas repetidas durante una misma oportunidad comercial.
    - mejora continuidad de experiencia para el consultor bajo presion de tiempo.
  - tradeoff:
    - se agrega complejidad operativa ligera por capa de cache distribuida.
  - validacion:
    - suite backend paso a 7 tests OK.

- 2026-02-28: backend plan fase 3B (calidad de evidencia) ejecutada.
  - objetivo tecnico:
    - separar verificacion de links del runtime para no afectar SLA de busqueda.
  - cambio:
    - nuevo job `verify_links_job.py` para actualizar `link_status` en Qdrant por lotes.
    - clasificador de link (`verified`, `inaccessible`, `unknown`) en tool de Qdrant.
  - por que negocio (breve):
    - mejora confiabilidad de evidencia que ve el consultor (menos links rotos/no verificables).
    - evita que propuestas se apoyen en casos sin respaldo accesible.
  - tradeoff:
    - job de mantenimiento adicional a operar (batch).
  - validacion:
    - suite backend paso a 9 tests OK.
- 2026-02-28: backend plan fase 4 (coordinacion de contrato y observabilidad) ejecutada.
  - objetivo tecnico:
    - asegurar contrato API estable y trazabilidad del flujo sin levantar servidor real en tests.
  - cambio:
    - se agregaron contract tests async para `/api/search` y `/agent/{thread_id}/state` (exito y errores tipificados).
    - logging de nodos HITL paso de `print` a `logger` estructurado.
  - por que negocio (breve):
    - reduce riesgo de romper frontend en medio de una oportunidad comercial.
    - mejora capacidad de diagnostico rapido cuando una propuesta falla bajo presion de tiempo.
  - tradeoff:
    - mayor disciplina de testing y logs, con leve costo de mantenimiento.
  - validacion:
    - suite backend paso a 12 tests OK.
- 2026-02-28: backend plan fase 5 (SLA y metricas operativas) ejecutada.
  - objetivo tecnico:
    - medir latencia real de busqueda (p50/p95/p99) y errores por categoria para control operativo.
  - cambio:
    - nuevo store de metricas en memoria (`SearchMetricsStore`).
    - `/api/search` ahora registra exitos y errores en metricas.
    - nuevo endpoint `GET /ops/metrics` (protegido por `ADMIN_TOKEN` en no-local).
  - por que negocio (breve):
    - permite detectar degradacion antes de afectar una propuesta en proceso comercial.
    - da visibilidad para decidir si escalar, reintentar o degradar de forma controlada.
  - tradeoff:
    - metricas locales (in-memory) se pierden en reinicio; suficiente para MVP, luego mover a observabilidad persistente.
  - validacion:
    - suite backend paso a 14 tests OK.
- 2026-02-28: frontend fase 1 (chat real + base visual premium) ejecutada.
  - objetivo tecnico:
    - reemplazar simulacion del chat por integracion real de refinamiento y establecer base visual corporativa.
  - cambio:
    - `ChatPanel` ahora usa `/agent/{thread_id}/refine` (sin mock local).
    - chat da feedback claro cuando falta sesion o propuesta previa.
    - propuesta se actualiza en store despues de cada refinamiento exitoso.
    - se aplico foundation visual premium (tokens, blobs, scanlines, glass cards, tipografia institucional).
    - fase `complete` ahora incluye panel de chat para refinamiento iterativo real.
  - por que negocio (breve):
    - evita “falsa funcionalidad” en demo y habilita refinamiento real en contexto comercial.
    - mejora percepcion de confianza y seniority visual frente a cliente interno/externo.
  - tradeoff:
    - mayor complejidad visual y de estado en frontend, pero sin romper contratos backend.
  - validacion:
    - `npm --prefix frontend-web run build` => OK.
- 2026-02-28: frontend fase 2 (consistencia premium + feedback operativo) ejecutada.
  - objetivo tecnico:
    - unificar formulario y cards al mismo sistema visual y hacer visibles errores API en flujo usuario.
  - cambio:
    - `InitialForm` migrado a glass/premium tokens con manejo de errores backend mas claro.
    - `CaseCard` migrado a estilo institucional dark + motion suave consistente.
    - `page.tsx` ahora muestra banners de error en fases `curating` y `complete`.
  - por que negocio (breve):
    - mejora legibilidad y confianza en momentos de decision comercial.
    - reduce friccion al diagnosticar fallos de generacion/refinamiento en vivo.
  - tradeoff:
    - mayor complejidad visual de estilos y estados en UI.
  - validacion:
    - `npm --prefix frontend-web run build` => OK.
- 2026-02-28: frontend fase 3 (navegacion flotante + responsive + motion) ejecutada.
  - objetivo tecnico:
    - mejorar orientacion de fase y coherencia de interaccion en desktop/mobile.
  - cambio:
    - navbar flotante premium con estado de fase y seleccion activa.
    - ajuste responsive para bloque propuesta + chat (sticky solo en anchos altos).
    - unificacion de transiciones/easing en las fases principales.
  - por que negocio (breve):
    - reduce perdida de contexto durante iteraciones en propuestas bajo presion de tiempo.
    - mejora lectura y control en presentacion interna del consultor.
  - tradeoff:
    - mayor densidad visual en header fijo, compensada con mejor navegabilidad.
  - validacion:
    - `npm --prefix frontend-web run build` => OK.
- 2026-02-28: frontend fase 4 (accesibilidad operativa + coherencia dark premium) ejecutada.
  - objetivo tecnico:
    - mejorar usabilidad real con teclado/lectores de pantalla y corregir contraste inconsistente en bloques de insight.
  - cambio:
    - `CaseCard` ahora soporta interaccion por teclado (`Enter`/`Space`) con `role`, `tabIndex` y `aria-pressed`.
    - `InitialForm` incorpora labels asociados, atributos ARIA por error, contador de caracteres y ayuda de campo en problema.
    - `ChatPanel` pasa a `form` semantico con boton submit deshabilitable y etiquetas ARIA.
    - `page.tsx` agrega `role="alert"` para errores y reestiliza `Top Match Global` al sistema visual dark institucional.
    - `globals.css` agrega `:focus-visible` global alineado al color acento.
  - por que negocio (breve):
    - reduce friccion en demos operativas y mejora control del consultor en sesiones largas de curacion/refinamiento.
    - minimiza fallos de percepcion (errores no visibles, foco perdido) en momentos criticos de propuesta comercial.
  - tradeoff:
    - mas detalles de implementacion UI a mantener, a cambio de una experiencia mas robusta y profesional.
  - validacion:
    - `npm --prefix frontend-web run build` => OK.
- 2026-02-28: frontend fase 5 (accesibilidad AA en flujo curating/complete) ejecutada.
  - objetivo tecnico:
    - fortalecer navegacion por teclado y semantica de interfaz en acciones criticas de seleccion/generacion/refinamiento.
  - cambio:
    - se agrego skip-link a contenido principal para acelerar navegacion por teclado.
    - botones clave de `page.tsx` incorporan `aria-label` y foco visible consistente.
    - contador de seleccion se publica en `aria-live` para feedback no visual.
    - `CaseCard` evita conflicto de interactivos anidados (se retiro `role=button` del contenedor) y mantiene seleccion accesible via boton dedicado.
    - `ChatPanel` mejora estado de envio (disabled visible + foco visible).
  - por que negocio (breve):
    - mejora control operativo del consultor cuando alterna rapido entre casos y propuesta.
    - reduce errores de interaccion en demos y sesiones de trabajo intensivo bajo presion comercial.
  - tradeoff:
    - mayor detalle de marcado ARIA y estados de foco a mantener en evoluciones futuras.
  - validacion:
    - `npm --prefix frontend-web run build` => OK.
