# 04 - Journey Map Completo

## Vision del flujo

Objetivo UX:
- Guiar al usuario de problema inicial a propuesta final en 20-30 minutos,
- Manteniendo control humano en decisiones clave.

## Fase 1 - Entrada de contexto (30-60 segundos)

Accion usuario:
- Ingresa empresa, rubro, area y problema.
- Selecciona switch (`NEO`, `AI`, `Ambos`).

Respuesta sistema:
- Valida datos.
- Crea `thread_id` y estado de sesion.

Criterio de salida:
- Input valido y sesion activa.

## Fase 2 - Busqueda de casos (10-20 segundos)

Accion usuario:
- Ejecuta busqueda.

Respuesta sistema:
- Genera embedding del problema.
- Consulta Qdrant con filtro segun switch.
- Devuelve casos ordenados por relevancia.

Criterio de salida:
- Lista de casos mostrada en tarjetas.

## Fase 3 - Curacion HITL (2-5 minutos)

Accion usuario:
- Revisa tarjetas.
- Selecciona casos mas aplicables.

Respuesta sistema:
- Guarda ids seleccionados en sesion.
- Habilita accion de generar propuesta.

Criterio de salida:
- Seleccion minima completada.

## Fase 4 - Generacion de propuesta (15-45 segundos)

Accion usuario:
- Solicita generacion.

Respuesta sistema:
- Compone prompt con contexto + casos.
- Genera borrador estructurado.
- Registra trazabilidad de fuentes.

Criterio de salida:
- Propuesta inicial visible y editable.

## Fase 5 - Refinamiento (opcional, 3-10 minutos)

Accion usuario:
- Pide ajustes (tono, foco, extension, riesgos, cierre).

Respuesta sistema:
- Aplica iteraciones por mensaje.
- Mantiene historial y versionado basico.

Criterio de salida:
- Version aprobada por usuario.

## Fase 6 - Exportacion y cierre (1-3 minutos)

Accion usuario:
- Exporta resultado.

Respuesta sistema:
- Entrega salida estructurada para compartir.
- Guarda metadata minima de ejecucion.

Criterio de salida:
- Propuesta lista para uso comercial.

## Estados de error y recuperacion

1. Qdrant vacio/no disponible:
- Mensaje claro de no disponibilidad.
- Opcion de reintento y guia de accion.

2. Error de generacion LLM:
- Mensaje controlado sin perder seleccion ni sesion.
- Reintento manual.

3. Timeout de servicios:
- Respuesta con fallback y registro en logs.

## KPIs de experiencia

1. Tiempo total de flujo <= 30 minutos.
2. Tiempo de busqueda <= 20 segundos.
3. Tasa de completitud end-to-end >= 80% en pruebas internas.
4. Satisfaccion de utilidad percibida >= 4/5.
