# INDICE DE DOCUMENTACION - NEO PROPOSAL AGENT

Fecha de corte: 2026-03-07
Version activa: V4 (NEO ELECTRIC MIDNIGHT — 6-screen wizard)
Rama activa: `feat/visual-refactor-v3`

## 1) Fuente de verdad

Leer primero — define estado real, riesgos y decisiones:
- `MVP-V2-DOCS/BITACORA_MVP_V2.md`

## 2) Documentos activos

### Arquitectura y Especificacion
| Archivo | Proposito |
|---------|-----------|
| `MVP-V2-DOCS/NEO_INTELLIGENCE_V4_SPEC.md` | Spec V4 completa: 6 pantallas, design system, API map, flujo usuario |
| `MVP-V2-DOCS/V4_COMPLETE_IMPLEMENTATION_GUIDE.md` | Guia de implementacion con code examples y roadmap por fases |
| `MVP-V2-DOCS/MVP-2.1-ARQUITECTURA-Y-LOGICA.md` | Arquitectura backend: storage, scoring, repositories, SLA |

### Operacional
| Archivo | Proposito |
|---------|-----------|
| `MVP-V2-DOCS/BITACORA_MVP_V2.md` | Bitacora operativa — log de cada sesion, errores, decisiones |

### Skills (Personas de agente)
| Archivo | Proposito |
|---------|-----------|
| `MVP-V2-DOCS/SKILLS/SKILL_BACKEND_EXPERT.md` | Persona backend: review protocol, engineering principles |
| `MVP-V2-DOCS/SKILLS/SKILL_FRONTEND_EXPERT.md` | Persona frontend: art direction, UX, a11y, motion (fusionado) |

### Raiz del proyecto
| Archivo | Proposito |
|---------|-----------|
| `README.md` | Setup, prerequisites, startup commands |
| `AI_INSTRUCTIONS.md` | Contexto global para agentes IA |
| `CLAUDE.md` | Reglas de workflow agentico |
| `frontend-web/README.md` | Instrucciones especificas del frontend |

### Archivo historico
| Archivo | Proposito |
|---------|-----------|
| `MVP-V1-DOCS/BITACORA_APRENDIZAJES.md` | Lecciones aprendidas de V1 (anti-patrones) |

## 3) Prioridad de actualizacion

P0 (obligatorio en cada cambio funcional):
1. `BITACORA_MVP_V2.md` — registrar sesion, errores, decisiones

P1 (alineacion de producto):
1. `NEO_INTELLIGENCE_V4_SPEC.md` — cualquier cambio de pantallas/flujo
2. `V4_COMPLETE_IMPLEMENTATION_GUIDE.md` — cambios de endpoints/modelos

P2 (estandares):
1. `SKILLS/SKILL_BACKEND_EXPERT.md`
2. `SKILLS/SKILL_FRONTEND_EXPERT.md`

## 4) Estado real por capa (2026-03-07)

Backend (FastAPI + LangGraph + Qdrant Cloud + Gemini):
- 27 rutas activas, 71/71 tests pass
- Graph: intake -> retrieve -> [INTERRUPT] -> update_summary -> draft
- Storage: SQLite (perfiles, radiografias, insights) + Qdrant Cloud (casos vectorizados)
- Collections: `neo_cases_v1` (95 pts), `neo_profiles_v1` (5 pts)
- Seed data: 13 perfiles empresa, 6 radiografias sector, 6 insights humanos

Frontend (Next.js 16 + Tailwind + Zustand):
- Design system: NEO ELECTRIC MIDNIGHT v4
- 6 pantallas wizard: EmptyState > ClientSelection > ActiveWorkspace > ProfileInsights > ProposalReview > TeamAssignment
- appStore como state manager principal (migrado de agentStore legacy)
- Build: OK, 0 errores TypeScript

## 5) Archivos eliminados (limpieza 2026-03-07)

Redundantes con V4 spec:
- `V4_IMPLEMENTATION_HANDOFF.md` (70% duplicado)
- `V4_INTEGRATION_MASTER_PLAN.md` (90% duplicado)

Obsoletos:
- `07-ESTADO-RAMAS-GIT-MVP2.md` (datos de ramas stale)
- `08-UI-UX-GUIDELINES.md` (contradice design system V4)
- `RUNBOOK_RELEASE_INTEL_BACKEND.md` (merge one-time ya completado)
- `MVP-V1-DOCS/PROJECT_DETAILS.md` (Streamlit-era, superseded)
- `MVP-V1-DOCS/RADIOGRAFIA_PROYECTO.md` (cleanup ya completado)

Fusionados:
- `SKILL_FRONTEND_ART_DIRECTION_EXPERT.md` + `SKILL_FRONTEND_UX_EXPERT.md` -> `SKILL_FRONTEND_EXPERT.md`
