# 02 - Requisitos Funcionales

## Convenciones

- Prioridad `P0`: critico para MVP.
- Prioridad `P1`: recomendable MVP si hay capacidad.
- Prioridad `P2`: Post-MVP.

## RF-01 Gestion de sesion y switch de coleccion (P0)

Descripcion:
- El sistema debe crear/retomar sesion por `thread_id`.
- El usuario debe elegir tipo de casos: `neo`, `ai`, `both`.

Criterios de aceptacion:
1. Se crea `thread_id` al iniciar flujo.
2. El switch afecta el filtro de busqueda.
3. Sesion continua entre pantallas del flujo.

## RF-02 Formulario de entrada inteligente (P0)

Descripcion:
- Captura minima: empresa, rubro, area, problema.

Criterios de aceptacion:
1. Validacion de campos obligatorios y longitudes.
2. Mensajes de error claros por campo.
3. No permite avanzar con input invalido.

## RF-03 Busqueda semantica de casos (P0)

Descripcion:
- Buscar similitud en `neo_cases_v1` con filtro por switch.

Criterios de aceptacion:
1. Retorna top N casos con `score` y payload util.
2. Si switch es `neo` o `ai`, aplica filtro correcto.
3. Si switch es `both`, no filtra por tipo.

## RF-04 Visualizacion y seleccion de casos (P0)

Descripcion:
- Mostrar resultados en tarjetas y permitir seleccion multiple.

Criterios de aceptacion:
1. Cada tarjeta muestra problema, solucion, impacto y fuente.
2. Seleccion/deseleccion sin recargar pagina.
3. Se exige minimo de casos seleccionados para continuar.

## RF-05 Generacion de propuesta inicial (P0)

Descripcion:
- Generar propuesta con los casos seleccionados.

Criterios de aceptacion:
1. Salida estructurada y trazable a casos usados.
2. Tiempo de respuesta aceptable para MVP.
3. Manejo de errores sin perder sesion.

## RF-06 Exportacion basica (P1)

Descripcion:
- Exportar propuesta en formato util para compartir.

Criterios de aceptacion:
1. Exporta texto estructurado (y PDF si esta disponible).
2. Incluye metadata minima (fecha, version, fuentes).

## RF-07 Persistencia de perfil de cliente (P1)

Descripcion:
- Guardar/actualizar perfil en `neo_profiles_v1`.

Criterios de aceptacion:
1. Upsert por empresa + area.
2. Puede reutilizarse en futuras propuestas.

## RF-08 Deteccion de base vacia y estado de salud (P0)

Descripcion:
- Detectar cuando Qdrant no tiene datos o no esta listo.

Criterios de aceptacion:
1. Endpoint `/health` refleja estado real de servicios.
2. UI muestra mensaje claro si no hay casos disponibles.
3. El flujo evita fallos silenciosos.

## RF-09 Validacion de datos y contratos (P0)

Descripcion:
- Validacion estricta en entradas y respuestas API.

Criterios de aceptacion:
1. Schemas versionados para requests/responses.
2. Errores 4xx para input invalido, 5xx para fallos internos.

## RF-10 Logging y trazabilidad (P1)

Descripcion:
- Registrar eventos clave del flujo.

Criterios de aceptacion:
1. Logs por `thread_id`.
2. Registro de latencia y errores por endpoint.

## RF-11 Refinamiento conversacional (P2)

Descripcion:
- Ajustar propuesta mediante chat iterativo.

Criterios de aceptacion:
1. Mantiene historial por sesion.
2. Permite generar nuevas versiones.

## RF-12 Inteligencia sectorial con cache (P2)

Descripcion:
- Enriquecimiento de contexto por rubro/area con TTL.

Criterios de aceptacion:
1. Primero consulta cache Redis.
2. Si no existe, consulta modelo y cachea resultado.

## Priorizacion de ejecucion recomendada

Sprint 1 (P0 base):
1. RF-01, RF-02, RF-03, RF-04, RF-08, RF-09

Sprint 2 (completitud MVP):
1. RF-05, RF-06, RF-07, RF-10

Sprint 3 (post-MVP):
1. RF-11, RF-12
