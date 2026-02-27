# Mapa de Ramas (Control Operativo)

Este archivo define para que existe cada rama y cuando usarla.

## Rama actual estable

- `master`
- Rol: base estable y punto de referencia principal del proyecto.
- Uso: solo cambios validados y listos para integrarse.

## Ramas activas del repositorio

- `deploy/mvp-v1`
- Rol: trabajo enfocado al despliegue de MVP V1.
- Uso: configuraciones y ajustes de release para V1.

- `feature/v2-fastapi-migration`
- Rol: desarrollo de la version V2 (migracion/refactor backend + frontend web).
- Uso: evolucion funcional de V2 sin mezclar con V1.

- `v2-refactor-wip`
- Rol: rama historica/WIP de refactor V2.
- Uso: referencia tecnica; no usar como rama principal de entrega.

## Ramas de seguridad

- `backup/v2-safety-20260226-190309`
- Rol: backup puntual de seguridad de V2.
- Uso: solo para recuperacion si algo falla.

## Reglas simples (anti-caos)

- V1 se trabaja en `deploy/mvp-v1`.
- V2 se trabaja en `feature/v2-fastapi-migration`.
- `master` no se usa para experimentos.
- Antes de cambiar de rama con cambios locales: `git stash push -u -m "WIP ..."` o commit.
- No borrar ramas de backup hasta terminar despliegue estable.

## Comandos rapidos

```bash
# Ver ramas
git branch -a

# Ir a master
git checkout master

# Ir a despliegue V1
git checkout deploy/mvp-v1

# Ir a trabajo V2
git checkout feature/v2-fastapi-migration

# Ver respaldos
git branch --list "backup/*"
git tag --list "safety/*"
git stash list
```
