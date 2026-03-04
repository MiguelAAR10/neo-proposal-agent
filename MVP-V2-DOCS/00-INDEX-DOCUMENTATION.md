# INDICE DE DOCUMENTACION - NEO PROPOSAL AGENT (MVP V2)

Fecha de corte: 2026-03-04
Version activa: MVP V2.1 integrado (frontend art + backend intelligence)
Baseline recomendado para frontend: `19cb88d5`
Baseline funcional V2.1 (busqueda + HITL + intel): `1cac68a8`

## 1) Fuente de verdad

Leer primero:
- `MVP-V2-DOCS/BITACORA_MVP_V2.md`

La bitacora define estado real por commit, riesgos y decisiones.

Control de ramas y versiones:
- `MVP-V2-DOCS/07-ESTADO-RAMAS-GIT-MVP2.md`

## 2) Estado real por capa

Backend:
- API activa: `/health`, `/api/search`, `/api/ingest`, `/agent/start`, `/agent/{thread_id}/select`, `/agent/{thread_id}/refine`, `/agent/{thread_id}/state`, `/ops/metrics`
- Servicio unificado de busqueda y contrato `/agent/*` alineado.
- `POST /agent/start` permite cliente no priorizado con `warning` y busqueda abierta centrada en problema.
- `Sales Insight Collector` HITL (`POST /intel/company/{company_id}/insights`) implementado con storage SQLite + patron Repository.

Frontend:
- Pantalla unica (`idle -> curating -> complete`) operativa.
- Chat conectado a `/agent/{thread_id}/refine` (ya no mock).
- Accesibilidad base: foco visible, ARIA, navegacion por teclado, mensajes de error.
- QA tecnico cerrado: `lint` y `build` OK.
- Rama activa de integracion: `feat/mvp2-frontend-art-two-panel` (unica rama operativa para evolucion V2).

## 3) Prioridad documental (actualizar siempre en este orden)

P0 (obligatorio en cada cambio funcional):
1. `MVP-V2-DOCS/BITACORA_MVP_V2.md`
2. `MVP-V2-DOCS/REQUIREMENTS/04-REQUISITOS-FUNCIONALES.md`
3. `MVP-V2-DOCS/REQUIREMENTS/05-REQUISITOS-TECNICOS.md`

P1 (alineacion de producto/arquitectura):
1. `MVP-V2-DOCS/MVP-2.1-ARQUITECTURA-Y-LOGICA.md`
2. `MVP-V2-DOCS/REQUIREMENTS/01-VISION-NEGOCIO.md`
3. `MVP-V2-DOCS/REQUIREMENTS/03-JOURNEY-MAPS.md`
4. `MVP-V2-DOCS/REQUIREMENTS/06-GUIA-DATOS-LOGOS-EMPRESA.md`

P2 (estandares de ejecucion):
1. `MVP-V2-DOCS/SKILLS/SKILL_BACKEND_EXPERT.md`
2. `MVP-V2-DOCS/SKILLS/SKILL_FRONTEND_UX_EXPERT.md`

## 4) Desalineaciones corregidas en esta actualizacion

1. Se elimina referencia a "ChatPanel mock" (ya esta integrado a backend).
2. Se elimina mezcla de prompts ajenos en la skill frontend.
3. Se unifica criterio de estado: `IMPLEMENTADO`, `PARCIAL`, `BACKLOG`.
4. Se fija decision de storage MVP: SQLite (SQLAlchemy) + Qdrant, sin Postgres/Mongo/Firestore.

## 5) Candidatos a depuracion

No eliminar documentos del set actual.

Si se requiere limpiar en siguiente ciclo:
1. Mantener `MVP-2.1-ARQUITECTURA-Y-LOGICA.md` como puente operativo de V2.1.
2. Evitar crear otro archivo paralelo de arquitectura V2.x; extender este mismo.
3. Consolidar cualquier nota suelta en bitacora en lugar de nuevos markdowns.

## 6) Plan de desarrollo de alto valor (ejecucion inmediata)

P0 - Impacto directo en propuesta comercial:
1. Estabilizar contrato `intel` con frontend (`/intel/company/{company_id}/insights`, `/intel/radar/run`).
2. Cerrar QA E2E sobre flujo principal (`start -> select -> proposal -> refine`).
3. Reducir errores operativos visibles (mensajes claros y fallback controlado en UI).

P1 - Confiabilidad operativa:
1. Persistir metricas clave de busqueda/chat (no solo in-memory).
2. Formalizar job operativo para calidad de links y reporte de rechazo de datos.
3. Endurecer seguridad de endpoints admin (token + rate limit baseline).

P2 - Escalamiento:
1. Diseñar migracion gradual de storage (`SQLite -> Postgres/pgvector`) sin romper dominio.
2. Versionar contratos API para cambios futuros de frontend.

Criterio de salida por sprint:
1. Cada entrega debe mapearse a un RF (archivo 04) y a un criterio tecnico (archivo 05).
2. Todo cambio en backend con impacto en payload debe incluir test de contrato.
3. Todo cambio visible en UI debe pasar `build` y registrar riesgo en bitacora.
