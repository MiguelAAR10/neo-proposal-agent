# RUNBOOK RELEASE - INTEL BACKEND (MERGE SAFE)

Fecha: 2026-03-02  
Scope: Integrar cambios backend/tools/docs de `feature/company-intel-orchestration-v1` sobre una laptop con versión local estable no pusheada, evitando conflictos con frontend.

## 1) Objetivo de Negocio

Publicar en GitHub una versión limpia que incluya:
- `Sales Insight Collector` endurecido (SQLite + Repository + tests).
- `GET /intel/company/{company_id}/profile`.
- `Macro-Intelligence Radar` (`POST /intel/radar/run`) con LangGraph + tools agentic.
- Dashboard Streamlit de pruebas con pestaña Macro Radar.
- Bitácora técnica conectada a impacto de negocio.

Sin romper:
- estabilidad local de la laptop,
- cambios estéticos no pusheados en `frontend-web/` y `frontend/`.

## 2) Regla de Oro Operativa

No mezclar en el mismo commit:
- cambios backend/docs/tools,
- cambios frontend visuales no relacionados.

Si aparece conflicto en `frontend-web/` o `frontend/`, preservar la versión estable local.

## 3) Commits Backend a Integrar

Cadena aprobada (en orden):

1. `eba1d33` `feat(backend-intel): implementar Sales Insight Collector y update_summary`
2. `8e594bb` `feat(intel-hardening): errores tipados + router modular + métricas + sqlalchemy estricto`
3. `eaa8624` `test(intel): integración real + regresiones de contrato + idempotencia`
4. `4740f70` `chore(tools): add isolated gradio UI for testing sales insights API`
5. `2488ba9` `feat(intel): add time-decay weights, departments and author dropdown for insights.`
6. `1adbcd0` `chore(tools): add streamlit tester UI with historical dummy data seeder`
7. `9451994` `fix(tools): add db hard-reset and historical time-series dummy data to streamlit tester.`
8. `9f89253` `fix(tools): ensure sqlite path creation for streamlit hard-reset seeder`
9. `4921e9f` `feat(intel): add profile read endpoint and stable contract tests`
10. `f2b84cd` `feat(intel): build agentic macro-intelligence radar with langgraph and external tools`
11. `fb25534` `feat(tools): add macro radar dashboard tab to streamlit tester`
12. `3e528f4` `docs(bitacora): register streamlit macro radar testing dashboard outcome`

## 4) Estrategia Recomendada (Laptop Estable = Source of Truth)

### Paso A - Preparación en laptop estable

```bash
git status
git branch --show-current
```

Si hay cambios locales críticos, crear respaldo:

```bash
git checkout -b backup/stable-pre-integration-20260302
git checkout <tu-rama-estable>
```

### Paso B - Traer commits backend sin tocar frontend

Opción recomendada: `cherry-pick` selectivo en rama de integración.

```bash
git checkout -b integration/intel-backend-radar
```

Si los commits ya están en remoto:

```bash
git fetch origin feature/company-intel-orchestration-v1
```

Si no están en remoto, usar bundle (offline transfer):

```bash
# En máquina origen:
git bundle create /tmp/intel_backend_tools.bundle eba1d33..3e528f4

# En laptop estable:
git fetch /ruta/intel_backend_tools.bundle feature/company-intel-orchestration-v1:tmp/intel-backend
```

Aplicar commits en orden:

```bash
git cherry-pick eba1d33 8e594bb eaa8624 4740f70 2488ba9 1adbcd0 9451994 9f89253 4921e9f f2b84cd fb25534 3e528f4
```

## 5) Manejo de Conflictos (Merge-Safe)

Si hay conflicto en `frontend-web/` o `frontend/`:

```bash
git restore --source=HEAD --staged --worktree frontend-web frontend
git add .
git cherry-pick --continue
```

Si conflicto en backend:
1. Mantener contratos API nuevos (`/intel/company/*`, `/intel/radar/run`).
2. Priorizar patrón Repository en SQLite.
3. Re-ejecutar tests antes de continuar.

Abortar integración si conflicto mayor:

```bash
git cherry-pick --abort
git checkout <tu-rama-estable>
```

## 6) Validación Técnica Obligatoria

Desde raíz del repo:

```bash
python -m unittest discover -s backend/tests -p 'test_*.py'
python -m py_compile scripts/admin_insight_tester.py
```

Validación API manual recomendada:

```bash
# Backend arriba en localhost:8000
curl -X POST http://localhost:8000/intel/radar/run \
  -H "Content-Type: application/json" \
  -d '{"industry_target":"Banca y Seguros","force_mock_tools":true}'
```

## 7) Checklist Pre-Push

- [ ] Rama de integración creada (`integration/intel-backend-radar`).
- [ ] Commits backend aplicados sin tocar frontend.
- [ ] Suite backend en verde.
- [ ] Script Streamlit compila.
- [ ] Bitácora incluye objetivo, cambio, tradeoff, validación e impacto negocio.
- [ ] Working tree limpio salvo cambios esperados.

## 8) Push y PR

```bash
git push -u origin integration/intel-backend-radar
```

PR recomendado:
- Base: rama estable principal del proyecto.
- Compare: `integration/intel-backend-radar`.
- Título sugerido: `Backend Intel Radar + Sales Insight Collector Hardening`.

## 9) Variables de Entorno para Modo Live Radar (Opcional)

En `.env`:

```env
RADAR_USE_LIVE_TOOLS=true
TAVILY_API_KEY=...
PERPLEXITY_API_KEY=...
FIRECRAWL_API_KEY=...
```

Opcional para ticker live:

```bash
pip install yfinance
```

Sin estas llaves, el radar funciona en modo mock (estable para QA).

## 10) Rollback Rápido

Si algo sale mal después de integrar:

```bash
git checkout <tu-rama-estable>
git branch -D integration/intel-backend-radar
```

Si ya pusheaste la rama de integración, simplemente cerrar PR (sin merge).

## 11) Entregable Final Esperado

Una rama de integración con:
- Backend intel/radar operativo.
- Tooling Streamlit para validación micro + macro.
- Documentación y bitácora alineadas negocio-técnica.
- Cero impacto en frontend estable local.
