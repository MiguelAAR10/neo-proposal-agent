# BITACORA MVP V2 - NEO PROPOSAL AGENT

Fecha de corte de este registro: **2026-02-28**

## 1. Proposito de esta bitacora

Esta bitacora documenta decisiones, aprendizajes y deuda tecnica de MVP V2 con una mirada arquitectonica. No reemplaza commits: los complementa explicando el razonamiento tecnico y de producto.

## 2. Donde esta hoy el MVP V2

### 2.1 Implementado

- Backend FastAPI con LangGraph y flujo HITL funcional.
- Persistencia de estado via checkpointer (MemorySaver y opcion Redis).
- Recuperacion de casos desde Qdrant con filtro por `switch` (`neo`, `ai`, `both`).
- Recuperacion de perfil cliente por empresa + area.
- Generacion de propuesta final con Gemini en `draft_node`.
- Frontend Next.js integrado al flujo principal `start -> select -> propuesta`.

### 2.2 Incompleto o desalineado

- El chat en `frontend-web/src/components/chat/ChatPanel.tsx` esta simulado, no integrado a un endpoint real.
- `frontend/app.py` (Streamlit legado) usa endpoints `/search` y `/chat` que no existen en la API V2 actual.
- Documentacion de arranque historicamente mezclada entre V1 y V2.

## 3. Arquitectura aplicada (real, no idealizada)

### 3.1 Principio rector

**Backend-First**: toda logica de negocio vive en backend; frontend solo orquesta interaccion de usuario y rendering.

### 3.2 Flujo operativo actual

1. `POST /agent/start`
2. LangGraph ejecuta `intake_node` y `retrieve_node`
3. Grafo se interrumpe antes de `draft_node`
4. Usuario selecciona casos
5. `POST /agent/{thread_id}/select`
6. Grafo reanuda y ejecuta `draft_node`
7. Propuesta final disponible en estado de sesion

### 3.3 Tradeoffs asumidos

- Se uso `MemorySaver` como fallback para reducir friccion local.
- Redis queda como camino de persistencia real para sesiones multi-instancia.
- Se priorizo cerrar el happy-path de propuesta antes del chat de refinamiento.

## 4. Aprendizajes tecnicos relevantes

### 4.1 Lo que funciono

- Separar nodos (`intake`, `retrieve`, `draft`) redujo acoplamiento.
- `interrupt_before=["draft_node"]` habilita HITL simple y controlable.
- Modelar request/response con Pydantic estabilizo contratos entre frontend y backend.

### 4.2 Lo que genero friccion

- Mantener dos frontends activos (Next.js y Streamlit) genero deriva de contratos.
- Documentacion sin fecha de corte facilito mezclar estado deseado vs estado real.
- Pruebas E2E dependen de servicios externos (Qdrant/Gemini), afectando reproducibilidad local.

### 4.3 Decisiones para evitar repeticion del problema

- Toda decision de arquitectura debe quedar en esta bitacora con fecha y contexto.
- README y scripts de arranque deben representar el flujo principal vigente, no el historico.
- Cambios de API deben incluir actualizacion explicita de clientes y docs en el mismo ciclo.

## 5. Plan de desarrollo V2 (arquitectonico-tecnico-creativo)

## Fase A - Alineacion de contrato (corto plazo)

- Consolidar API publica V2 como unica fuente de verdad para UI productiva.
- Marcar Streamlit como legacy en docs y evitar que parezca ruta oficial.
- Incorporar pruebas de contrato para endpoints `start/select/state`.

## Fase B - Conversacional real (valor diferencial)

- Diseñar endpoint de chat contextual por `thread_id`.
- Reusar estado LangGraph para responder sobre casos seleccionados y propuesta activa.
- Reemplazar mock de `ChatPanel` por integracion real con manejo de errores y loading states.

## Fase C - Robustez operativa (escalabilidad)

- Mover persistencia a Redis en entornos compartidos.
- Agregar health checks reales (Qdrant/Redis/Gemini) y telemetria basica.
- Definir estrategia de timeouts/retries por dependencia externa.

## Fase D - Calidad de propuesta (ventaja competitiva)

- Versionado de propuestas (`v1`, `v2`, ...) con historial y rollback.
- Refinamientos guiados por prompts estructurados (tono, longitud, enfoque).
- Metricas de calidad: claridad ejecutiva, evidencia de casos, impacto de negocio.

## 6. Riesgos vigentes y mitigacion

- Riesgo: deuda por doble frontend.
  - Mitigacion: foco en Next.js como canal primario y legacy explicitado.
- Riesgo: fallas silenciosas en servicios externos.
  - Mitigacion: health checks y errores tipificados en API.
- Riesgo: drift documental.
  - Mitigacion: fecha de corte y seccion "estado real" obligatoria en docs V2.

## 7. Regla para commits con pensamiento arquitectonico

Cada commit de impacto tecnico debe responder, en el mensaje o PR:

1. Que problema sistemico corrige.
2. Que decision de arquitectura materializa.
3. Que tradeoff acepta.
4. Que deuda abre o cierra.

Plantilla sugerida:

`tipo(scope): cambio`

- problema: ...
- decision: ...
- tradeoff: ...
- deuda: ...

## 8. Registro de actualizacion de esta bitacora

- **2026-02-28**: Se actualiza estado real del MVP V2, se documenta desalineacion Streamlit/Next.js y se fija plan por fases.
