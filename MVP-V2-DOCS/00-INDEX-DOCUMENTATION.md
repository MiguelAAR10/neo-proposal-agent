# INDICE DE DOCUMENTACION - NEO PROPOSAL AGENT (MVP V2)

Fecha de corte: 2026-02-28
Version activa: MVP V2.1 estable + cierre frontend QA
Baseline recomendado para frontend: `7344c78c`
Baseline funcional V2.1 (busqueda + HITL): `15bfc20b`

## 1) Fuente de verdad

Leer primero:
- `MVP-V2-DOCS/BITACORA_MVP_V2.md`

La bitacora define estado real por commit, riesgos y decisiones.

## 2) Estado real por capa

Backend:
- API activa: `/health`, `/api/search`, `/api/ingest`, `/agent/start`, `/agent/{thread_id}/select`, `/agent/{thread_id}/refine`, `/agent/{thread_id}/state`, `/ops/metrics`
- Servicio unificado de busqueda y contrato `/agent/*` alineado.

Frontend:
- Pantalla unica (`idle -> curating -> complete`) operativa.
- Chat conectado a `/agent/{thread_id}/refine` (ya no mock).
- Accesibilidad base: foco visible, ARIA, navegacion por teclado, mensajes de error.
- QA tecnico cerrado: `lint` y `build` OK.

## 3) Prioridad documental (actualizar siempre en este orden)

P0 (obligatorio en cada cambio funcional):
1. `MVP-V2-DOCS/BITACORA_MVP_V2.md`
2. `MVP-V2-DOCS/REQUIREMENTS/04-REQUISITOS-FUNCIONALES.md`
3. `MVP-V2-DOCS/REQUIREMENTS/05-REQUISITOS-TECNICOS.md`

P1 (alineacion de producto/arquitectura):
1. `MVP-V2-DOCS/MVP-2.1-ARQUITECTURA-Y-LOGICA.md`
2. `MVP-V2-DOCS/REQUIREMENTS/01-VISION-NEGOCIO.md`
3. `MVP-V2-DOCS/REQUIREMENTS/03-JOURNEY-MAPS.md`

P2 (estandares de ejecucion):
1. `MVP-V2-DOCS/SKILLS/SKILL_BACKEND_EXPERT.md`
2. `MVP-V2-DOCS/SKILLS/SKILL_FRONTEND_UX_EXPERT.md`

## 4) Desalineaciones corregidas en esta actualizacion

1. Se elimina referencia a "ChatPanel mock" (ya esta integrado a backend).
2. Se elimina mezcla de prompts ajenos en la skill frontend.
3. Se unifica criterio de estado: `IMPLEMENTADO`, `PARCIAL`, `BACKLOG`.

## 5) Candidatos a depuracion

No eliminar documentos del set actual.

Si se requiere limpiar en siguiente ciclo:
1. Mantener `MVP-2.1-ARQUITECTURA-Y-LOGICA.md` como puente operativo de V2.1.
2. Evitar crear otro archivo paralelo de arquitectura V2.x; extender este mismo.
3. Consolidar cualquier nota suelta en bitacora en lugar de nuevos markdowns.

