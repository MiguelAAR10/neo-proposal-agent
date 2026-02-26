# 03 - Arquitectura Tecnica

## Objetivo tecnico

Definir una arquitectura robusta para V2 web que:
1. Sea desarrollable de forma incremental.
2. Sea estable en local y staging.
3. Permita evolucion a produccion sin rehacer el core.

## Arquitectura objetivo

```text
Frontend (Next.js)
  -> consume API HTTP
Backend (FastAPI + LangGraph)
  -> Qdrant (busqueda vectorial)
  -> Redis (sesion + cache)
  -> Gemini (embeddings + generacion)
```

## Componentes

Frontend:
- Next.js + React + TypeScript.
- UI split-screen: formulario, tarjetas, panel de propuesta/chat.

Backend:
- FastAPI para contratos HTTP.
- LangGraph para orquestar nodos del flujo.
- Servicios desacoplados: search, proposal, profile, health.

Datos:
- Qdrant `neo_cases_v1`: casos y benchmarks.
- Qdrant `neo_profiles_v1`: memoria de cliente por contexto.
- Redis: sesion (`thread_id`) y cache sectorial con TTL.

LLM:
- Embeddings: `gemini-embedding-001`.
- Generacion: modelo Gemini Flash vigente.

## Estructura recomendada (monorepo actual)

```text
backend/
  src/
    api/
    agent/
    tools/
frontend/
  app.py (o migracion progresiva a Next.js separado)
neo-proposal-specs/
  requirements/
  skills/
```

Nota:
- En MVP se puede mantener monorepo para velocidad.
- Para produccion, separar repos backend/frontend es preferible.

## Contrato API minimo (MVP)

1. `POST /agent/start`
- Crea sesion y retorna `thread_id`.

2. `POST /agent/{thread_id}/search`
- Ejecuta busqueda por similitud segun switch.

3. `POST /agent/{thread_id}/select`
- Recibe ids seleccionados y genera propuesta inicial.

4. `POST /agent/{thread_id}/profile`
- Guarda/actualiza perfil de cliente.

5. `GET /health`
- Estado de API, Qdrant, Redis y disponibilidad de modelo.

## Contratos de datos minimos

Caso (`neo_cases_v1`) debe incluir:
- id
- tipo (`NEO` o `AI`)
- industria
- area
- problema
- solucion
- beneficios
- tecnologias
- url_slide
- contexto_embedding

Perfil (`neo_profiles_v1`) debe incluir:
- id
- empresa
- industria
- area
- objetivos
- decisor
- notas
- ultima_actualizacion

## Reglas de resiliencia obligatorias

1. Inicializacion en `lifespan`:
- Qdrant, Redis y clientes LLM no se crean como variables globales.

2. Indices Qdrant previos a produccion:
- Validar indices de payload usados por filtros (`tipo`, `industria`, `area`).

3. Timeouts y retry:
- Llamadas externas con timeout explicito y retry exponencial.

4. Degradacion controlada:
- Si falla enriquecimiento sectorial, el flujo principal no debe colapsar.

5. Observabilidad:
- Log estructurado por `thread_id`, endpoint, latencia y error.

## Seguridad y configuracion

Variables de entorno minimas:
- `GEMINI_API_KEY`
- `QDRANT_URL`
- `QDRANT_API_KEY` (si aplica)
- `REDIS_URL`
- `ALLOWED_ORIGINS`

Buenas practicas:
- Sin secretos hardcodeados.
- CORS restringido por ambiente.
- Validacion de payload en borde de API.

## Estrategia de despliegue web

Local:
- `docker compose` para Qdrant + Redis.
- Backend y frontend ejecutados con hot reload.

Staging:
- Frontend en hosting web (ej. Vercel).
- Backend en servicio HTTP persistente (ej. Render/Fly/AWS).
- Qdrant y Redis administrados o autoalojados con backups.

Produccion:
- Escalado horizontal del backend.
- Redis y Qdrant con alta disponibilidad.
- Monitoreo y alertas.
