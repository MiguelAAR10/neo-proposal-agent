# MVD - ERRORES CRITICOS DE ARQUITECTURA Y LOGICA DE DATOS

Fecha: 2026-02-28
Rama: `fix/arquitectura-logica-datos-mvd`
Estado: Analisis y plan de correccion (sin cambios de codigo)

## 1) Sintomas visibles vs causa raiz

### Sintomas actuales
- Score mostrado sin explicacion clara (ej. "71%" magico).
- Casos sin URL utilizable ("Sin slide").
- Campos de perfil vacios (objetivos/pain points).
- Propuesta generica y sin cuantificacion.
- Inconsistencia de seleccion ("0 seleccionados" sin mecanismo claro).

### Causa raiz
1. **Metadata incompleta en casos**: URLs, KPIs y calidad de payload no garantizados.
2. **Perfil de cliente no cargado correctamente**: backend no distingue entre "no existe" y "vacio".
3. **Generacion sin contexto de seleccion**: LLM no recibe casos elegidos de forma robusta.
4. **Scoring opaco**: falta descomposicion de relevancia en componentes trazables.
5. **Fases mezcladas**: intake/selection/generation sin boundaries operativas estrictas.

## 2) Flujo objetivo (V2 fixed)

### Fase 0 - Intake + Search
Backend debe devolver en una sola respuesta:
- `cases[]` con metadata completa,
- `profile` (si existe),
- `sector_intel` (cacheado o generado),
- score transparente por caso.

Frontend debe mostrar:
- perfil con fallback explicito (`no_mapeado`),
- casos con URL/KPI/score explicable,
- mensaje de accion: seleccionar >= 1 para generar.

### Fase 1 - Curation (HITL)
- Seleccion explicita por case_id.
- Estado `selected_cases` persistido por `thread_id`.
- Cambio de seleccion debe afectar contexto de generacion.

### Fase 2 - Generation
- Prompt estructurado con:
  - contexto cliente (objetivos/pains),
  - casos seleccionados,
  - intel sector,
  - requirement de cuantificacion (KPI).

### Fase 3 - Refinement
- Iteracion sobre propuesta previa.
- Versionado `v1/v2/v3...` en estado.
- Historial coherente por `thread_id`.

## 3) Arquitectura de datos necesaria

### 3.1 Coleccion `neo_cases_v1`
Campos minimos obligatorios:
- `id`, `tipo`, `empresa`, `industria`, `area`,
- `titulo`, `problema`, `solucion`,
- `beneficios`, `kpi_principal`,
- `url_slide`, `embedding_context`,
- `confianza_fuente`, `data_quality_score`, `fecha_ingesta`.

### 3.2 Coleccion `neo_profiles_v1`
Campos minimos:
- `id`, `empresa`, `area`, `industria`,
- `objetivos[]`, `pain_points[]`,
- `notas`, `decisor`, `ciclo_compra`.

### 3.3 Redis `sector_intel`
Clave recomendada:
- `sector:{industria}:{area}`
Contenido:
- tendencias,
- benchmarks,
- oportunidades,
- TTL definido (ej. 30 dias).

## 4) Problemas especificos y solucion

### Problema A - Score "magico"
Solucion:
- Descomponer score en:
  - similitud semantica,
  - match industria,
  - match area,
  - confianza fuente,
  - recencia.
- Retornar `score_raw`, `score_label`, `score_breakdown`.

### Problema B - Casos sin URL/KPI
Solucion:
- En ingesta: quality gates.
- Si faltan campos criticos, marcar `incomplete` y excluir de top resultados productivos.
- Mostrar `data_quality_score` en frontend.

### Problema C - Perfil vacio
Solucion:
- Query de perfil por `empresa+area`.
- Diferenciar estados:
  - `profile_status=found`,
  - `profile_status=not_found`,
  - `profile_status=incomplete`.

### Problema D - Generacion generica
Solucion:
- Forzar uso de `selected_case_ids` en prompt builder.
- Si seleccion vacia: bloquear generacion o pedir confirmacion explicita.
- Respuesta debe incluir referencias a casos usados.

### Problema E - HITL roto
Solucion:
- Separar endpoints/fases de manera estricta:
  - `start` (intake+search),
  - `select` (curation state),
  - `generate/refine` (produccion de propuesta).

## 5) Priorizacion de correccion (tecnico)

### P0 (bloqueante)
1. Garantizar seleccion explicita + propagacion a generacion.
2. Garantizar score transparente con breakdown.
3. Garantizar metadata minima (URL/KPI) en resultados.

### P1
1. Carga robusta de perfil cliente con estados.
2. Enriquecimiento de sector por cache.
3. Versionado de propuesta y trazabilidad por thread.

### P2
1. Dashboard operativo de calidad y latencia.
2. DLQ y backoffice para casos incompletos.

## 6) Criterios de salida de este MVD

Se considera corregido cuando:
1. No hay casos visibles sin metadata critica en flujo comercial.
2. Usuario entiende por que cada caso es relevante.
3. Propuesta cita casos seleccionados y aporta cuantificacion.
4. El flujo HITL esta separado y verificable E2E.

