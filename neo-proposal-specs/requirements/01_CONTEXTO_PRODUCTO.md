# 01 - Contexto de Producto

## Proposito

NEO Proposal Agent V2 acelera la creacion de propuestas comerciales para consultoria.

Meta principal:
- Pasar de 4-6 horas manuales a 20-30 minutos por propuesta,
- Sin perder calidad narrativa ni evidencia de soporte.

## Usuario principal

Persona clave: consultor junior ("el joven").

Dolores actuales:
- Alto tiempo de preparacion.
- Dificultad para reutilizar conocimiento historico.
- Calidad variable segun experiencia individual.
- Poca personalizacion por industria y area.

## Resultado esperado

El sistema debe permitir:
1. Capturar contexto del cliente.
2. Buscar casos relevantes (NEO, AI o ambos).
3. Permitir seleccion humana (HITL) de casos.
4. Generar borrador de propuesta.
5. Refinar y exportar salida util para presentacion.

## Valor para negocio

1. Productividad: reduccion de tiempo de preparacion.
2. Calidad: propuestas con evidencia trazable.
3. Escalabilidad: consultores junior con mejor performance.
4. Memoria institucional: datos y aprendizaje reutilizable.

## Fuentes de informacion

Triangulacion de contexto:
1. Casos historicos y benchmarks (coleccion `neo_cases_v1`).
2. Perfil de cliente y area (coleccion `neo_profiles_v1`).
3. Inteligencia sectorial con cache en Redis.

## Principios no negociables aprendidos de V1

1. Modelos vigentes: usar `gemini-embedding-001` para embeddings.
2. Inicializacion segura: clientes externos solo en `lifespan` (no globals).
3. Qdrant con indices de payload obligatorios antes de exponer busqueda.
4. Backend con contratos estables y frontend desacoplado por API.

## Alcance

MVP (fase de reconstruccion):
- Intake, busqueda, curacion HITL, generacion, persistencia de sesion, health checks.

Post-MVP:
- Refinamiento conversacional avanzado,
- Inteligencia sectorial extendida,
- Admin y analitica avanzada.

## Criterios de exito MVP

1. Flujo end-to-end sin bloqueos funcionales.
2. Respuesta util de casos con trazabilidad.
3. Generacion de propuesta usable en entorno real.
4. Estabilidad en entorno local y staging web.
