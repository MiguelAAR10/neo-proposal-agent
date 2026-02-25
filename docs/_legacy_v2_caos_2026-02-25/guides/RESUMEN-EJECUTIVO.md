# RESUMEN EJECUTIVO - NEO PROPOSAL AGENT V2

## 1) Objetivo

Construir una V2 del NEO Proposal Agent que permita a consultores generar propuestas comerciales de alta calidad en 20-30 minutos, usando evidencia real (casos), contexto de cliente (perfil) e inteligencia sectorial.

## 2) Problema de Negocio

- Tiempo actual para propuesta manual: 4-6 horas.
- Calidad inconsistente entre consultores.
- Bajo reaprovechamiento del conocimiento institucional.
- Poca personalizacion por cliente/rubro/area.

## 3) Resultado Esperado (MVP V2)

- Flujo completo: intake -> busqueda -> seleccion HITL -> generacion -> refinamiento basico -> exportacion.
- Busqueda semantica en Qdrant con switch de coleccion (NEO / AI / Ambos).
- Propuesta en formato slide-ready con referencias trazables.
- Base tecnica lista para escalar (FastAPI + LangGraph + Redis + Qdrant + Next.js).

## 4) Arquitectura Objetivo

- Frontend: Next.js 14 + React + Tailwind + Zustand + TanStack Query.
- Backend: FastAPI + LangGraph (estado por thread_id).
- Datos:
  - `neo_cases_v1`: casos de exito.
  - `neo_profiles_v1`: perfiles cliente/area.
- Cache y sesion: Redis (TTL por tipo de dato).
- IA:
  - Embeddings: `gemini-embedding-001`.
  - Generacion: Gemini Flash con retry y timeouts.

## 5) Alcance MVP vs Post-MVP

### MVP (desarrollar primero)

- RF-01, RF-02, RF-03, RF-04, RF-06, RF-11, RF-13.
- Endpoints base `/agent/*` + `/health`.
- Ingesta validada con schema unico de payload y payload indexes.

### Post-MVP

- RF-05, RF-07, RF-08 completo, RF-09, RF-10, RF-12, RF-14+.
- Admin avanzado, observabilidad extendida y analitica de conversion.

## 6) Riesgos Clave y Mitigacion

- Inconsistencia documental/tecnica -> congelar contrato API y schemas antes de codificar.
- Colecciones o indexes incompletos en Qdrant -> validacion de salud al arranque.
- Latencia/costo LLM -> cache Redis + retries + limites.
- Estado de conversacion no persistente -> checkpointer Redis y `thread_id` obligatorio.

## 7) Plan de Ejecucion Recomendado

1. Definir contrato final (API, payload, colecciones, switch).
2. Consolidar ingesta y normalizacion de datos.
3. Implementar backend MVP con pruebas.
4. Implementar frontend MVP conectado al backend.
5. Integrar refinamiento y exportacion.
6. Endurecimiento (testing, observabilidad, despliegue).

## 8) Criterio de Exito del MVP

- Usuario completa flujo end-to-end sin bloqueo.
- Tiempo objetivo <= 30 minutos por propuesta.
- Recuperacion de casos relevante con trazabilidad.
- Estabilidad funcional en entorno local y staging.

## 9) Estado Documental

- Documentacion revisada y alineada para iniciar desarrollo V2.
- Modelo de embedding oficial unificado: `gemini-embedding-001`.
- Fecha de actualizacion: 25 de febrero de 2026.
