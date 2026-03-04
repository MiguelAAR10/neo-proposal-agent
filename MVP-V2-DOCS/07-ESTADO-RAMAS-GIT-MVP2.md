# ESTADO DE RAMAS GIT/GITHUB - MVP2

Fecha de corte: 2026-03-04  
Repositorio: `git@github.com:MiguelAAR10/neo-proposal-agent.git`

## 1) Resumen Ejecutivo

- El desarrollo activo de MVP2 está en `feat/mvp2-frontend-art-two-panel` (`1cac68a8`).
- `origin/feature/company-intel-orchestration-v1` ya está contenido dentro de la rama activa MVP2.
- `origin/feature/v2-fastapi-migration` es una base histórica de arranque MVP2, también contenida por la rama activa.
- `master` va por una línea separada (6 commits que no están en la rama MVP2).
- Existe una rama local sin remoto: `chore/integrate-company-intel-2026-03-03`.

Conclusión operativa: para trabajo de MVP2, la rama de referencia actual es `feat/mvp2-frontend-art-two-panel`.

## 2) Inventario Real de Ramas

### Ramas locales

1. `master` -> trackea `origin/master` (sin divergencia)
2. `feat/mvp2-frontend-art-two-panel` -> trackea `origin/feat/mvp2-frontend-art-two-panel` (sin divergencia)
3. `chore/integrate-company-intel-2026-03-03` -> sin upstream (solo local)

### Ramas remotas (GitHub)

1. `origin/master`
2. `origin/feat/mvp2-frontend-art-two-panel`
3. `origin/feature/company-intel-orchestration-v1`
4. `origin/feature/v2-fastapi-migration`

### Relación local vs remoto

- Sincronizadas (mismo nombre y tracking):
1. `master` <-> `origin/master`
2. `feat/mvp2-frontend-art-two-panel` <-> `origin/feat/mvp2-frontend-art-two-panel`

- Solo local:
1. `chore/integrate-company-intel-2026-03-03`

- Solo remoto:
1. `origin/feature/company-intel-orchestration-v1`
2. `origin/feature/v2-fastapi-migration`

## 3) Topología y Etapas de MVP2

```text
master (línea separada) ----------------------------- 7c5e0fee
                           \
                            19c4facc  origin/feature/v2-fastapi-migration   (base MVP2)
                              |
                            7f983784  safety/mvp2.1-pre-dev-20260227-225946
                              |
                            9b689b70  origin/feature/company-intel-orchestration-v1
                              |\
                              | \- c722d3eb -> 0b3c52f3  chore/integrate-company-intel-2026-03-03 (local docs/integración)
                              |
                              \- ... -> 19cb88d5 -> cbf406f1 -> 0e4c25f9 -> 392d0d4d -> 3e182b1d -> 1cac68a8
                                                           feat/mvp2-frontend-art-two-panel (rama activa MVP2)
```

## 4) Diferencias Entre Ramas (ahead/behind)

Formato: `A...B = commits_unicos_en_A | commits_unicos_en_B`

1. `master...feat/mvp2-frontend-art-two-panel = 6 | 59`
2. `master...origin/feature/company-intel-orchestration-v1 = 6 | 53`
3. `master...origin/feature/v2-fastapi-migration = 6 | 3`
4. `feat/mvp2-frontend-art-two-panel...origin/feature/company-intel-orchestration-v1 = 6 | 0`
5. `feat/mvp2-frontend-art-two-panel...origin/feature/v2-fastapi-migration = 56 | 0`
6. `feat/mvp2-frontend-art-two-panel...chore/integrate-company-intel-2026-03-03 = 6 | 2`

Lectura clave:
- `feature/company-intel-orchestration-v1` y `feature/v2-fastapi-migration` ya quedaron absorbidas por la rama activa MVP2.
- `master` no es ancestro directo de la rama MVP2 actual; es una línea paralela.

## 5) Qué Hace Cada Rama

1. `master`
- Línea estable separada con cambios de soporte V1/Streamlit y docs puntuales.
- Último commit: `7c5e0fee` ("fix: eliminar linea redundante que pisaba el API_URL").

2. `origin/feature/v2-fastapi-migration`
- Etapa base de migración técnica a FastAPI + Next.js.
- Commit ancla: `19c4facc`.

3. `origin/feature/company-intel-orchestration-v1`
- Etapa de integración de inteligencia (collector, radar, contratos y hardening).
- Commit ancla: `9b689b70`.

4. `feat/mvp2-frontend-art-two-panel` (activa)
- Evolución de UX/art direction y flujo integral MVP2 encima de `company-intel`.
- Último commit: `1cac68a8`.
- Incluye los 6 commits más recientes sobre `company-intel`.

5. `chore/integrate-company-intel-2026-03-03` (local)
- Rama operativa temporal de integración/documentación.
- No está publicada en GitHub y no debe asumirse como fuente oficial.

## 6) Criterio de No Mezcla (etapas que no deben cruzarse sin plan)

1. No mezclar cambios ad hoc de `master` a MVP2 por merge directo.
- Si se requiere un fix puntual de `master`, usar `cherry-pick` de commit específico y validar contratos V2.

2. No desarrollar features nuevas en `origin/feature/v2-fastapi-migration` ni en `origin/feature/company-intel-orchestration-v1`.
- Son etapas históricas de referencia, no ramas objetivo actuales.

3. La rama de trabajo para MVP2 debe partir de `feat/mvp2-frontend-art-two-panel`.

## 7) Comandos Operativos (entrar/cambiar/ver versiones)

### Sincronizar y ver estado

```bash
git fetch --all --prune
git status --short --branch
git branch -vv
git branch -a
```

### Cambiar de rama

```bash
git switch feat/mvp2-frontend-art-two-panel
git switch master
```

### Crear local tracking para una rama remota que no existe localmente

```bash
git switch -c feature/company-intel-orchestration-v1 --track origin/feature/company-intel-orchestration-v1
git switch -c feature/v2-fastapi-migration --track origin/feature/v2-fastapi-migration
```

### Ver relación entre dos ramas

```bash
git rev-list --left-right --count master...feat/mvp2-frontend-art-two-panel
git log --graph --oneline --decorate --all --simplify-by-decoration
git diff --stat master..feat/mvp2-frontend-art-two-panel
```

### Ver hitos/versiones MVP2 por commit y tags

```bash
git tag --list --sort=creatordate
git show -s --format='%h %ad %d %s' --date=short 19c4facc 7f983784 9b689b70 1cac68a8
```

## 8) Estandarización de Nombres (recomendación)

Problema actual:
- Coexisten prefijos `feat/` y `feature/`.
- Hay ramas remotas sin local tracking.
- Hay ramas locales temporales sin convención de lifecycle.

Propuesta mínima (sin romper historial):
1. Para nuevas ramas de producto: usar solo `feature/<scope>`.
2. Para tareas técnicas no funcionales: `chore/<scope>`.
3. Para documentación: `docs/<scope>`.
4. Mantener local y remoto con el mismo nombre cuando exista upstream.
5. Marcar ramas históricas de etapa como `archive/*` cuando se congelen.

Ejemplo de transición recomendada:
1. `feat/mvp2-frontend-art-two-panel` -> `feature/mvp2-frontend-art-two-panel` (en una ventana controlada).
2. `feature/v2-fastapi-migration` -> `archive/v2-fastapi-migration`.
3. `feature/company-intel-orchestration-v1` -> `archive/company-intel-orchestration-v1`.

## 9) Ruta Recomendada de Trabajo (MVP2 generado)

1. Basarse siempre en `feat/mvp2-frontend-art-two-panel` para cambios nuevos de MVP2.
2. Crear ramas hijas cortas:
- `feature/mvp2-<modulo>-<objetivo>`
3. Validar antes de merge:
- tests backend
- build frontend-web
- actualización de `MVP-V2-DOCS/BITACORA_MVP_V2.md`
4. Integrar por PR hacia la rama activa MVP2, no hacia ramas históricas.
