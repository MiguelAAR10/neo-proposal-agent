# SKILL - Backend Expert

## Mision

Implementar el backend V2 con FastAPI + LangGraph + Qdrant + Redis,
con contratos estables, observabilidad y tolerancia a fallos.

## Stack obligatorio

- Python 3.11+
- FastAPI
- Pydantic v2
- LangGraph
- qdrant-client
- redis (async)
- tenacity
- pytest + pytest-asyncio

## Responsabilidades

1. Contratos API claros y versionables.
2. Flujo del agente desacoplado en nodos.
3. Busqueda semantica con filtros consistentes.
4. Persistencia de sesion por `thread_id`.
5. Health checks reales de dependencias.

## Estructura minima recomendada

```text
backend/
  src/
    api/
      main.py
      routes_agent.py
      routes_health.py
    agent/
      graph.py
      nodes.py
      state.py
    tools/
      qdrant_tool.py
      profile_tool.py
      sector_tool.py
    config.py
```

## Contratos minimos que debes implementar

1. `POST /agent/start`
2. `POST /agent/{thread_id}/search`
3. `POST /agent/{thread_id}/select`
4. `POST /agent/{thread_id}/profile`
5. `GET /health`

## Reglas tecnicas no negociables

1. Lifespan:
- Inicializar clientes externos dentro de `lifespan`.
- No crear clientes globales al importar modulos.

2. Validacion:
- Request/response con schemas Pydantic.
- Errores 4xx para input y 5xx para fallos internos.

3. Qdrant:
- Verificar existencia de colecciones e indices al arranque.
- Filtrar por `tipo`, `industria`, `area` segun contrato.

4. Resiliencia:
- Retry exponencial y timeout para LLM/servicios remotos.
- Degradar en enriquecimiento sin romper flujo principal.

5. Trazabilidad:
- Log estructurado por `thread_id`, endpoint y latencia.

## Checklist de implementacion

1. Configuracion de entorno cargada desde `.env`.
2. Health check integrado a arranque.
3. Busqueda semantica validada con datos reales.
4. Sesion persistente entre llamadas HTTP.
5. Manejo de errores consistente para frontend.

## Checklist de testing

1. Unit tests de validadores y nodos principales.
2. Integration tests para endpoints del flujo MVP.
3. Prueba de arranque con servicios caidos (Qdrant/Redis).
4. Prueba de carga basica (latencia por endpoint).

## Definition of Done (Backend)

1. Flujo MVP backend funcional end-to-end.
2. OpenAPI util para consumo frontend.
3. Logs utiles para depurar sin inspeccion manual excesiva.
4. Documentacion de variables y endpoints actualizada.
