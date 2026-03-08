# BITÁCORA MVP V3 - PROPUESTA EJECUTIVA Y NORMALIZACIÓN

Fecha de corte: 2026-03-08
Versión objetivo: **MVP V3 - Propuesta Ejecutiva Premium**
Rama activa: `feat/visual-refactor-v3`
Commits clave: `5dffddc0` → `c0b4cf27`

## 1) Propósito

Esta bitácora documenta la evolución del MVP V2 hacia V3, centrada en:
- **Propuesta ejecutiva tipo PPT** con formato limpio y profesional
- **Normalización backend** de markdown → estructura estable
- **Eliminación de fragilidad** en parsing frontend
- **Mejoras UX**: paneles colapsables, casos opcionales, 3 equipos enfocados

---

## 2) Estado Final Implementado

### Backend
- **Normalizer robusto** (`_normalize_proposal_to_structure`)
  - Tolera múltiples formatos de headers (canónico, "Sección N", variantes)
  - Extrae 6 secciones: diagnóstico, solución, arquitectura, impacto, roadmap, siguiente_paso
  - Limpia artifacts markdown (`**`, `[tags]`)
  - Fallbacks seguros para secciones faltantes
- **proposal_structured** en ProposalState y AgentStateResponse
- **Tests completos**: 78/78 passing (71 previos + 7 normalizer)

### Frontend
- **ProposalReview refactorizado**
  - Consume `proposal_structured` como prioridad
  - Fallback a parsing markdown solo legacy
  - Grid 2x3 ejecutivo con iconos y colores
  - Tags tecnológicos extraídos automáticamente
- **Paneles colapsables** (sidebar + top context)
  - Estado en appStore: `sidebarCollapsed`, `topPanelsCollapsed`
  - Botones toggle con animaciones CSS
  - Chat expande cuando contexto colapsa
- **Casos opcionales**
  - Botón generar habilitado sin selección
  - Backend maneja `case_ids: []` correctamente
- **3 equipos enfocados**
  - Analytics & AI/ML: Dashboards, Data Engineering, Cloud
  - AI Lab: AI Engineering, LLM/RAG, Agents, GenAI
  - Growth & Marketing Digital: Marketing, CRM, Growth

### TeamAssignment
- **Resumen inteligente** consume `proposal_structured`
- Parser tolerante con fallback a markdown
- **Caso de respaldo** con link externo si disponible
- Limpieza de artifacts en textos mostrados

---

## 3) Matriz de Trazabilidad por Commit

| Commit | Fecha | Objetivo | Archivos Clave | Resultado |
|--------|-------|----------|----------------|-----------|
| `5dffddc0` | 2026-03-08 | Casos opcionales | `schemas.py`, `nodes.py`, `useDashboardController.ts` | ✅ casos_seleccionados_ids acepta [] |
| `000c2ba5` | 2026-03-08 | Paneles colapsables | `appStore.ts`, `ActiveWorkspace.tsx`, `globals.css` | ✅ sidebar y top-context toggleables |
| `6afdc5e0` | 2026-03-08 | Formato ejecutivo | `nodes.py` (prompt), `ProposalReview.tsx` | ✅ 6 secciones + parser visual |
| `3893ad3c` | 2026-03-08 | Streamline + 3 equipos | `ProposalReview.tsx`, `agent.py` | ✅ panel único limpio + 3 teams |
| `84cb9291` | 2026-03-08 | Backend normalizer | `nodes.py`, `state.py`, `schemas.py` | ✅ proposal_structured estable |
| `e4858d8b` | 2026-03-08 | Frontend consume estructura | `ProposalReview.tsx`, `appStore.ts`, `useApi.ts` | ✅ parseStructured() priority |
| `62590a34` | 2026-03-08 | Tests normalizer | `test_proposal_normalizer.py` | ✅ 7 tests, 78/78 total |
| `c0b4cf27` | 2026-03-08 | TeamAssignment mejoras | `TeamAssignment.tsx` | ✅ resumen + link respaldo |

---

## 4) Decisiones de Arquitectura Críticas

### 4.1) Cirugía de Normalización (commits 84cb9291 → 62590a34)

**Problema detectado:**
- Frontend parseaba markdown con regex frágiles
- Cada variación del LLM rompía la UI
- Código duplicado visible, secciones faltantes

**Solución quirúrgica:**
```
LLM (markdown libre)
  → Backend: _normalize_proposal_to_structure()
      → proposal_structured (contrato estable)
          → Frontend: parseStructured() [priority]
          → Frontend: parseMarkdownFallback() [legacy]
```

**Beneficios:**
- Contrato estable entre backend-frontend
- Tolerancia a variaciones del LLM
- Fallbacks seguros (nunca UI rota)
- Artifacts limpiados server-side

### 4.2) Paneles Colapsables (commit 000c2ba5)

**Motivación:**
- Consultores necesitan flexibilidad de layout
- Chat panel pequeño en workspace original
- Contexto a veces no necesario visible

**Implementación:**
- Estado Zustand: `sidebarCollapsed`, `topPanelsCollapsed`
- CSS transitions sin romper grid existente
- Chat auto-expande cuando top colapsa

### 4.3) Casos Opcionales (commit 5dffddc0)

**Cambio conceptual:**
- **Antes**: Casos obligatorios como base de propuesta
- **Ahora**: Casos como "evidencia de apoyo opcional"

**Mensaje al LLM ajustado:**
```markdown
No se seleccionaron casos de referencia. Esta propuesta
se genera como **solución original** basada en las
capacidades de NEO y el contexto del cliente.
```

---

## 5) Aprendizajes y Mejores Prácticas

### 5.1) Prompt Engineering para Normalización

**Lección:** LLMs varían output incluso con instrucciones estrictas.

**Patrones tolerantes exitosos:**
```python
patterns = {
    'diagnostico': [
        r'###?\s*🔍\s*DIAGNÓSTICO',  # Canónico
        r'Sección\s*1[:.]?\s*🔍',     # Legacy
        r'###?\s*Diagnóstico',        # Sin emoji
    ],
}
```

**Fallbacks seguros obligatorios:**
```python
if not result['diagnostico']:
    result['diagnostico'] = ['Análisis del problema en proceso']
```

### 5.2) Contratos Estables Backend → Frontend

**Anti-pattern evitado:**
```typescript
// ❌ MAL: Frontend parsea markdown directamente
const sections = markdown.split(/###/).map(...)
```

**Pattern correcto:**
```typescript
// ✅ BIEN: Frontend consume estructura del backend
const sections = parseStructured(data.proposal_structured)
if (!sections.length) {
  // Fallback solo si falla backend
  sections = parseMarkdownFallback(data.propuesta_final)
}
```

### 5.3) Tests con Fixtures Reales

**Ficción del MVP V3:**
```python
# Fixture 1: Markdown canónico
MARKDOWN_CANONICAL = """
### 🔍 DIAGNÓSTICO
- Alto costo operativo...
"""

# Fixture 2: Formato "Sección N" (legacy)
MARKDOWN_SECCION_FORMAT = """
Sección 1: 🔍 Diagnóstico del Problema
- Procesos manuales...
"""

# Fixture 3: Con duplicados y artifacts
# Fixture 4: Parcial (sección faltante)
```

**Coverage:**
- Formatos múltiples ✅
- Artifacts y duplicados ✅
- Límites (5 bullets, 8 tags) ✅
- Entrada vacía (fallbacks) ✅

---

## 6) Problemas Resueltos Durante Implementación

### 6.1) Puerto 8000 en uso
**Error:** `[Errno 98] Address already in use`
**Causa:** Proceso uvicorn previo no terminado
**Fix:** `kill -9 <PID>` antes de reiniciar
**Prevención:** Usar único terminal o systemd service

### 6.2) Módulo src.main no encontrado
**Error:** `Could not import module "src.main"`
**Causa:** ASGI entry point en `src/api/main.py`, no `src/main.py`
**Fix:** `uvicorn src.api.main:app --reload --port 8000`
**Documentado en:** commit `fa4604e1`

### 6.3) Frontend caché obsoleto
**Síntoma:** Cambios no visibles después de build
**Causa:** `.next/` cache no invalidado
**Fix:** `rm -rf .next && npm run dev`
**Lección:** Siempre reiniciar dev server después de cambios estructurales

---

## 7) Métricas Finales MVP V3

| Métrica | V2 | V3 | Δ |
|---------|----|----|---|
| Tests backend | 71 | 78 | +7 |
| Componentes refactorizados | - | 3 | ProposalReview, ActiveWorkspace, TeamAssignment |
| Líneas código normalizer | 0 | 144 | +144 |
| Paneles colapsables | 0 | 2 | sidebar + top-context |
| Equipos consultoria | 4 | 3 | -1 (enfoque) |
| Parsing robusto | ❌ | ✅ | Tolerante + fallbacks |

### Coverage de Tests
```
backend/tests/
├── test_proposal_normalizer.py ✅ (7 tests nuevos)
├── ... 71 tests existentes ✅
Total: 78/78 passing
```

### Build Status
```
Backend: ✅ Todos los tests pasan
Frontend: ✅ Build exitoso (Next.js 16)
Lint: ✅ Sin errores
```

---

## 8) Prompt Templates Clave

### 8.1) Draft Node - Propuesta Ejecutiva

```markdown
Genera la propuesta con **EXACTAMENTE** estas 6 secciones:

### 🔍 DIAGNÓSTICO
- Reformula el problema en lenguaje ejecutivo (máx 3 bullets)
- Identifica impacto cuantificable

### 💡 SOLUCIÓN PROPUESTA
- Términos de valor de negocio (no solo tecnología)
- Máximo 4 bullets con beneficios claros

### 🏗️ ARQUITECTURA Y STACK
- Componentes clave en bullets
- Stack como tags: `[Python]` `[React]` `[PostgreSQL]`

### 📊 IMPACTO Y KPIs
- KPIs cuantificables: **Métrica:** Valor
- Máximo 4-5 KPIs relevantes

### 🗓️ ROADMAP
- **Fase 1 (Quick Win):** Entregable
- **Fase 2 (Consolidación):** Milestone
- **Fase 3 (Optimización):** Visión

### 🎯 SIGUIENTE PASO
- Acción concreta e inmediata
- Qué necesitas del cliente

**300-500 palabras total** — Profundo pero conciso
```

### 8.2) Normalizer - Patrones Tolerantes

```python
def _normalize_proposal_to_structure(markdown_text: str) -> dict:
    """
    Tolera:
    - ### 🔍 DIAGNÓSTICO (canónico)
    - Sección 1: 🔍 Diagnóstico (legacy)
    - ## 🔍 DIAGNÓSTICO (variante)

    Devuelve:
    {
        'diagnostico': ['bullet 1', 'bullet 2'],
        'solucion': ['bullet 1', ...],
        'arquitectura': {
            'bullets': ['...'],
            'tags': ['Python', 'React']
        },
        'impacto': [...],
        'roadmap': [...],
        'siguiente_paso': [...]
    }

    Límites:
    - Max 5 bullets por sección
    - Max 8 tech tags
    - Fallbacks: nunca null, siempre contenido por defecto
    """
```

---

## 9) Contexto de Negocio y Estrategia

### Problema Original
NEO generaba propuestas ricas en contenido pero:
- **Formato inconsistente** → difícil de presentar a cliente
- **Parsing frágil** → UI rota con variaciones LLM
- **Sin flexibilidad de layout** → chat panel pequeño
- **Casos obligatorios** → limitaba creatividad

### Solución MVP V3
- **Backend normaliza** → contrato estable
- **Frontend consume** → UI siempre funcional
- **Paneles ajustables** → workflow flexible
- **Casos opcionales** → propuestas originales posibles

### Valor para Consultores
1. Propuestas **presentation-ready** (PPT format)
2. **Zero errores** por parsing (backend garantiza estructura)
3. **Layout adaptable** según tarea (más chat o más contexto)
4. **Más creatividad** (no depender de casos históricos)

---

## 10) Next Steps (Post-MVP V3)

### Corto Plazo (Sprint Siguiente)
- [ ] Agregar **refine** endpoint a normalizer
- [ ] **Cache** de proposal_structured en Redis
- [ ] **Export to PDF** para envío a cliente
- [ ] **Historial** de propuestas generadas

### Mediano Plazo
- [ ] **A/B testing** de prompts
- [ ] **ML feedback loop** de éxito de propuestas
- [ ] **Templates** pre-configurados por industria
- [ ] **Colaboración** multi-usuario en propuesta

### Largo Plazo (V4)
- [ ] **Agente autónomo** genera + refina sin HITL
- [ ] **Integración Salesforce** para tracking
- [ ] **Analytics** de tasa de éxito por tipo de propuesta

---

## 11) Comandos de Verificación

### Local Development
```bash
# Backend
cd backend
uvicorn src.api.main:app --reload --port 8000

# Frontend
cd frontend-web
npm run dev

# Tests
cd backend
pytest tests/ -v
```

### Health Checks
```bash
# Backend health
curl http://127.0.0.1:8000/health

# Frontend build
cd frontend-web
npm run build && npm start
```

### Deploy (cuando esté listo)
```bash
git push origin feat/visual-refactor-v3
# CI/CD toma el relevo
```

---

## 12) Referencias y Contexto Técnico

### Stack
- **Backend:** FastAPI + LangGraph + Qdrant + SQLite
- **Frontend:** Next.js 16 + Zustand + TanStack Query
- **LLM:** Gemini (via LangChain)
- **Tests:** pytest (78 tests)

### Commits Baseline Importantes
- `eb6e72d0` - Visual V4 baseline (NEO ELECTRIC MIDNIGHT)
- `5dffddc0` - Casos opcionales (cambio conceptual)
- `84cb9291` - Normalizer backend (arquitectura clave)

### Documentación Relacionada
- `MVP-V1-DOCS/BITACORA_APRENDIZAJES.md` - Fundamentos
- `MVP-V2-DOCS/BITACORA_MVP_V2.md` - Evolución V2
- `MVP-V2-DOCS/MVP-2.1-ARQUITECTURA-Y-LOGICA.md` - Arquitectura LangGraph

---

**Estado final:** MVP V3 sólido, testeado, documentado.
**Listo para:** Push a remoto + revisión de equipo.
