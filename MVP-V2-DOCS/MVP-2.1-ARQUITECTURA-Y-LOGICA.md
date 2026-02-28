# MVP 2.1 - Arquitectura, Logica de Datos y Sistema Visual

Fecha: 2026-02-28
Estado: Documento rector para ejecucion tecnica de MVP 2.1
Alcance: End-to-end desde ingesta de casos hasta propuesta basada en evidencia

## 1. Critica dura al estado anterior (V2 base)

La version anterior habilito un flujo HITL basico, pero fallo en lo mas importante: calidad y trazabilidad de evidencia.

Fallas estructurales observadas:

1. Contrato de datos incompleto.
- Los casos pueden llegar sin URL util, sin KPI, sin solucion clara o sin beneficios cuantificados.
- Resultado: tarjetas sin valor comercial y propuesta debil.

2. Desacople entre busqueda semantica y explicabilidad.
- Existe score numerico, pero no se explica en lenguaje de negocio.
- Resultado: el consultor no entiende por que un caso es relevante.

3. Perfil cliente con matching rigido.
- Si empresa+area no coincide exacto, el sistema degrada a placeholder.
- Resultado: contexto del cliente vacio o pobre.

4. Ingesta no institucionalizada como producto.
- Faltan reglas duras de validacion y rechazo por calidad minima.
- Resultado: la base vectorial se llena con payload irregular.

5. Coexistencia de rutas legacy y rutas V2.
- Diferentes contratos de API (legacy y V2) generan confusion operativa.
- Resultado: desalineacion entre frontend, backend y documentacion.

Diagnostico ejecutivo:
- El cuello de botella no es UX.
- El cuello de botella es arquitectura de datos + contrato semantico + gobernanza de evidencia.

## 2. Objetivo final de MVP 2.1

Construir un motor de evidencia comercial que entregue, para cada problema del cliente:

1. Casos relevantes y verificables (con URL y KPI).
2. Jerarquia de confianza (NEO primero, AI despues cuando aplique).
3. Contexto para propuesta anclada (no generica).
4. Flujo HITL real: buscar -> curar -> generar -> refinar.

Metricas objetivo:

- 90%+ de casos retornados con `url_slide` valida.
- 85%+ de casos retornados con `kpi_impacto` no vacio.
- p95 de busqueda < 700 ms (considerando embedding remoto).
- 0 respuestas de propuesta usando casos no seleccionados.

## 3. Principios tecnicos no negociables

## 3.1 Vector semantico separado de metadata

- Vector solo representa significado del caso (problema, solucion, beneficios, contexto).
- Metadata conserva evidencia intacta (URL, empresa, stack, KPI, origen, fecha, etc).
- Nunca vectorizar URL ni campos administrativos.

## 3.2 Single Source of Truth en Qdrant

- CSV solo es fuente de ingesta.
- Runtime busca siempre en Qdrant.
- No mezclar lecturas ad-hoc al CSV durante consultas de producto.

## 3.3 Contrato de calidad de caso

Un caso sin evidencia minima no entra al indice productivo.

Campos obligatorios de entrada:

- `case_id`
- `tipo` (`NEO` o `AI`)
- `titulo`
- `problema`
- `solucion`
- `url_slide`
- `kpi_impacto` o `beneficios` no vacios

## 3.4 Transparencia de relevancia

- Mostrar score crudo para trazabilidad interna.
- Exponer label y confidence para usuario final.
- Filtrar scores por debajo de umbral operativo.

## 3.5 Jerarquia de confianza controlada

En `switch = ambos`:

1. Priorizar presentacion de casos NEO.
2. Conservar score de similitud real en cada item.
3. No ocultar mejores matches AI; solo se prioriza orden visual y narrativa comercial.

## 4. Arquitectura funcional de MVP 2.1

## 4.1 Fase A - Ingesta y normalizacion

Pipeline:

1. Leer `ai_cases.csv` y `neo_legacy.csv`.
2. Validar fila por fila con reglas minimas.
3. Normalizar al schema unico.
4. Construir `texto_embedding`.
5. Generar embedding con `gemini-embedding-001`.
6. Upsert batch en `neo_cases_v1`.
7. Ejecutar validaciones post-ingesta y generar reporte.

Politica de rechazo:

- URL invalida: reject.
- `problema` vacio: reject.
- `solucion` vacia: reject.
- Sin KPI y sin beneficios: reject.
- Duplicado de `case_id`: update deterministico.

## 4.2 Fase B - Search runtime

1. Validar input (`problema`, `switch`).
2. Generar embedding del problema.
3. Buscar en Qdrant con filtro por `tipo`.
4. Aplicar `score_threshold`.
5. En `ambos`, aplicar orden de confianza NEO->AI.
6. Traducir score a `score_label` + `confidence`.
7. Retornar JSON de casos listo para UI.

## 4.3 Fase C - Curation HITL

1. Usuario selecciona 1..N casos de la lista.
2. Sistema persiste `selected_case_ids` por `thread_id`.
3. Si cambia seleccion, invalida contexto de propuesta anterior.

## 4.4 Fase D - Generation

Prompt de propuesta debe incluir obligatoriamente:

- Problema del cliente.
- Perfil cliente (o estado explicitado de ausencia).
- Casos seleccionados con su evidencia.
- KPI de referencia por caso.
- Diferenciacion entre evidencia NEO y benchmark AI.

Regla:
- Si `selected_case_ids` esta vacio, no se genera propuesta.

## 4.5 Fase E - Refinement versionado

- Cada refinamiento crea `propuesta_version_n`.
- Se guarda `reason_of_change` y timestamp.
- Se puede volver a una version anterior sin regenerar todo.

## 5. Modelo de datos unificado para casos

```json
{
  "case_id": "NEO-BANCA-002",
  "tipo": "NEO",
  "origen": "neo_legacy.csv",
  "titulo": "User feedback analysis para BCP",
  "empresa": "BCP",
  "industria": "Banca",
  "area": "Customer Experience",
  "problema": "Analisis manual y lento de feedback digital",
  "solucion": "Pipeline NLP + dashboard de insights",
  "beneficios": [
    "Decision en tiempo real",
    "Reduccion de ciclo de analisis"
  ],
  "stack": ["NLP", "BI", "Dashboard"],
  "kpi_impacto": "88% automatizacion de analisis",
  "url_slide": "https://docs.google.com/presentation/...",
  "texto_embedding": "Titulo: ... Problema: ... Solucion: ... Beneficios: ...",
  "score_raw": 0.87,
  "score_label": "Muy relevante",
  "confidence": "87% match",
  "confianza_fuente": 1.0,
  "fecha_ingesta": "2026-02-28"
}
```

## 6. Contrato API objetivo (MVP 2.1)

Nota: el contrato final debe consolidarse en una sola familia de endpoints para evitar deriva.

## 6.1 Endpoint de busqueda

`POST /api/search`

Request:

```json
{
  "problema": "Mejorar decisiones de credit scoring",
  "switch": "ambos"
}
```

Response:

```json
{
  "status": "success",
  "total": 6,
  "switch_usado": "ambos",
  "latencia_ms": 520,
  "casos": []
}
```

## 6.2 Endpoint de seleccion

`POST /api/session/{thread_id}/selection`

- Persiste seleccion de casos.
- Devuelve estado de curacion.

## 6.3 Endpoint de generacion

`POST /api/session/{thread_id}/proposal/generate`

- Requiere seleccion minima de 1 caso.
- Devuelve propuesta v1.

## 6.4 Endpoint de refinamiento

`POST /api/session/{thread_id}/proposal/refine`

- Recibe instruccion de ajuste.
- Devuelve propuesta vN y versionado.

## 7. Sistema visual (UI) para evidenciar valor

Este bloque define como debe verse el producto para reforzar confianza, no decoracion.

## 7.1 Principio visual rector

Cada pantalla debe responder: "Que evidencia tengo, por que confio, que decision tomo ahora".

## 7.2 Jerarquia visual de cada tarjeta de caso

Orden obligatorio de bloques:

1. Header de confianza:
- badge tipo (`NEO` o `AI`)
- score_label + confidence

2. Evidencia del caso:
- titulo
- empresa + area + industria
- problema resumido
- solucion resumida

3. Impacto:
- KPI principal en alto contraste
- lista corta de beneficios

4. Verificacion:
- boton `Ver slide original`
- indicador de disponibilidad de URL

5. Accion HITL:
- selector explicito (`Seleccionar caso`)

## 7.3 Tokens visuales sugeridos

- NEO: fondo neutro con acento verde/teal (confianza ejecutada).
- AI: fondo neutro con acento azul/ambar (benchmark).
- KPI: bloque de alta legibilidad con contraste AA.
- Alertas de calidad de dato: ambar (incompleto) o rojo (invalidado).

## 7.4 Microcopy de negocio

Reemplazar etiquetas tecnicas ambiguas:

- `Score: 0.87` -> `Muy relevante (87% match con tu problema)`
- `Slide no disponible` -> `Evidencia no verificable` (y despriorizar caso)
- `0 seleccionados` -> `Selecciona al menos 1 caso para generar propuesta`

## 8. Reglas de calidad y observabilidad

## 8.1 Data quality gates

En ingesta registrar:

- total filas
- validas
- rechazadas
- razones de rechazo por categoria
- cobertura de URL
- cobertura de KPI

## 8.2 Runtime quality

Por busqueda registrar:

- latencia embedding
- latencia qdrant
- total retornado
- distribucion NEO/AI
- porcentaje con URL valida
- top1 score

## 8.3 Generation quality

Por propuesta registrar:

- cantidad de casos seleccionados
- porcentaje de casos con KPI
- longitud de salida
- deteccion de referencias a casos seleccionados

## 9. Riesgos y mitigaciones

1. Riesgo: payload incompleto por ingesta flexible.
- Mitigacion: rechazar filas sin evidencia minima.

2. Riesgo: contrato API doble (legacy vs V2.1).
- Mitigacion: congelar contrato unico y deprecacion formal de legacy.

3. Riesgo: baja explicabilidad del ranking.
- Mitigacion: score_label + confidence + score_raw en logs.

4. Riesgo: propuesta generica.
- Mitigacion: bloquear generacion sin seleccion y KPI de soporte.

## 10. Plan de ejecucion por etapas

Etapa 1 - Data foundation:
- cerrar schema unico y validadores
- ingesta deterministica y reporte
- cobertura de URL y KPI

Etapa 2 - Search contract:
- endpoint unico de busqueda
- score transparente
- jerarquia NEO primero en modo ambos

Etapa 3 - HITL robusto:
- seleccion persistida por sesion
- generacion estrictamente basada en seleccion
- invalidacion controlada al cambiar seleccion

Etapa 4 - Refinement con versionado:
- v1, v2, v3 con trazabilidad
- rollback entre versiones

## 11. Definicion de listo (DoD) para MVP 2.1

Un incremento de MVP 2.1 se considera listo solo si cumple todo:

1. Data:
- 90%+ de casos con URL valida y KPI presente.

2. Search:
- respuesta con score explicable y sin casos por debajo de umbral.

3. HITL:
- flujo buscar->seleccionar->generar operativo sin bypass.

4. Proposal:
- menciona explicitamente los casos seleccionados.

5. Observabilidad:
- logs y metricas minimas activas.

6. Documentacion:
- actualizacion de bitacora y contrato en cada cambio estructural.

## 12. Resumen ejecutivo final

MVP 2.1 no es "hacer mas UI".

MVP 2.1 es formalizar un sistema de evidencia comercial:

- dato confiable,
- ranking explicable,
- seleccion humana real,
- generacion anclada en casos verificables.

Si falla cualquiera de esas cuatro capas, el producto vuelve a producir propuestas genericas.

