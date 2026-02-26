# 01 - VISIÓN Y CONTEXTO DEL NEGOCIO

## Propósito del Producto

**NEO Proposal Agent** es una herramienta estratégica que acelera la creación de propuestas comerciales de consultoría, permitiendo que consultores junior generen propuestas de impacto en **20 minutos** en lugar de 6 horas.

El sistema triangula tres fuentes de inteligencia:
1. **Casos de éxito** (historial NEO + benchmarks externos)
2. **Perfiles de cliente** (memoria de objetivos por empresa/área)
3. **Inteligencia de sector** (tendencias, benchmarks, oportunidades)

---

## El Problema que Resuelve

### Para el Consultor Junior ("El Joven")
- Tarda 4-6 horas en crear una propuesta desde cero
- No tiene acceso sistemático a casos previos relevantes
- Propuestas carecen de contexto sectorial y de cliente específico
- Presión de tiempo en licitaciones y oportunidades urgentes

### Para NEO (Organización)
- Pérdida de conocimiento institucional cuando consultores senior se van
- Inconsistencia en calidad de propuestas
- Baja tasa de conversión por falta de personalización
- Subutilización de casos ganados previos

---

## Valor Estratégico Generado

| Dimensión | Métrica | Impacto |
|-----------|---------|--------|
| **Velocidad** | 6 horas → 20 minutos | 18x más rápido |
| **Calidad** | Propuestas data-driven con casos comprobados | Mayor credibilidad |
| **Conversión** | Personalización con inteligencia de cliente | +15-25% tasa de cierre |
| **Escalabilidad** | Consultores junior producen como senior | Capacidad sin contratar |
| **Conocimiento** | Memoria institucional explícita | Retención de IP |

---

## Usuario Principal: "El Joven"

**Perfil:**
- Consultor junior del equipo de clientes NEO
- 1-3 años de experiencia
- Conoce la herramienta, no memoriza todos los casos
- Bajo presión de tiempo en licitaciones

**Necesidades:**
- Generar propuestas rápidas sin perder calidad
- Inspiración de casos previos para adaptar
- Confianza en que la propuesta es relevante
- Capacidad de personalizar según cliente

**Comportamiento esperado:**
- Entra a la web cuando tiene una oportunidad
- Ingresa datos del cliente (empresa, área, problema)
- Busca casos similares
- Selecciona los más relevantes
- Genera propuesta en minutos
- Refina si es necesario
- Exporta y presenta

---

## Origen de los Datos: Scraper de PDFs

Los casos provienen de un proceso automatizado:

1. **Input:** PDFs de presentaciones de venta NEO (pitches, propuestas ganadas, case studies)
2. **Proceso:**
   - Extracción de diapositivas (una por caso)
   - OCR y limpieza de texto
   - Enriquecimiento con Gemini (generar contexto para embedding)
   - Normalización a CSV

3. **Output:** Dos tipos de CSV con estructuras diferentes

### Estructura CSV Tipo A: AI/Benchmarks Externos

Estos casos vienen de presentaciones sobre soluciones de IA, con estructura comercial clara:

```
id                    | BENCH-001, BENCH-002, ...
tipo                  | "AI"
origen_detectado      | "BENCH" (externo)
trigger_comercial     | "Reducción 30% costos" (KPI que llama atención)
kpi_impacto          | "30% reducción en 3 meses"
area_mejora          | "Operaciones", "Marketing", "Ventas", etc.
problema             | Descripción del dolor específico
solucion             | Qué se implementó (nombre simple y entendible)
beneficios           | Resultados cuantitativos
tecnologias          | "LLMs, RPA, Python" (stack usado)
url_slide            | Link a diapositiva original en Drive/PDF
contexto_para_embedding | Texto enriquecido para vectorizar (CURADO)
```

**Ejemplo real:**
```
trigger_comercial: "Automatización de reportes: 40% reducción de tiempo"
problema: "Equipo de 5 analistas dedica 60% del tiempo a reportes manuales en Excel"
solucion: "Agentes IA para validación y generación automática de reportes"
beneficios: "40% reducción en tiempo, 0 errores manuales, escalable a 10x volumen"
tecnologias: "LLMs, Python, Power BI, RPA"
```

### Estructura CSV Tipo B: NEO Históricos (Legacy)

Estos casos vienen de proyectos reales ejecutados por NEO, con estructura más operativa:

```
id                    | NEO-001, NEO-042, ...
tipo                  | "NEO"
origen_detectado      | "NEO" (interno)
proyecto              | "Automatización TechCorp"
cliente               | "TechCorp"
industria             | "Tecnología"
area                  | "Operaciones"
objetivo              | "Reducir tiempo procesamiento 30%"
solucion              | "Implementación de RPA + Python"
resultado             | "25% reducción en 3 meses, ROI 5:1"
url_slide             | Link a evidencia/presentación
```

**Ejemplo real:**
```
proyecto: "Automatización de Procesos Financieros - Banco ABC"
cliente: "Banco ABC"
objetivo: "Reducir tiempo de cierre mensual de 5 días a 2 días"
solucion: "Implementación de RPA para validación de transacciones + ML para detección de anomalías"
resultado: "Cierre en 2 días, 0 excepciones no detectadas, ahorro $500K anuales"
```

---

## Principios de Diseño del Producto

### 1. Tecnología es Transversal
- **No filtrar por stack tecnológico**
- Un caso de "LLMs" es relevante para "Computer Vision" si el problema es similar
- La solución es el patrón, no la tecnología específica

### 2. Área es Mínima (No Restrictiva)
- Área es contexto, no filtro
- Contenido se busca por similitud semántica, no por área exacta
- Área solo se usa para enriquecimiento de perfil

### 3. HITL (Human-in-the-Loop)
- El sistema sugiere, el consultor decide
- Nunca generar propuesta sin aprobación de casos
- Permitir 0 casos seleccionados (aunque no recomendado)

### 4. Output Slide-Ready
- Contenido breve, impactante, para presentar
- Cada propuesta debe caber en 1-2 slides
- URLs clickeables para verificación

### 5. Memoria Institucional
- Cada interacción enriquece el sistema
- Perfiles de cliente se actualizan
- Casos se marcan como "útiles" o "no relevantes"

---

## Flujo de Valor: De Oportunidad a Propuesta

```
┌─────────────────────────────────────────────────────────────┐
│ TRIGGER: Licitación o cliente menciona necesidad            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ FASE 1: INTAKE (30 segundos)                                │
│ - Joven ingresa: empresa, industria, área, problema         │
│ - Elige switch: "Casos NEO" / "Benchmarks AI" / "Ambos"    │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ FASE 2: BÚSQUEDA (10 segundos)                              │
│ - Sistema busca casos similares en Qdrant                   │
│ - Retorna 6-8 casos ordenados por relevancia                │
│ - Muestra en tarjetas con KPI, problema, solución           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ FASE 3: CURACIÓN (5 minutos)                                │
│ - Joven selecciona casos relevantes (0 a N)                 │
│ - Chat para refinar búsqueda si es necesario                │
│ - Puede ver slides originales (URLs clickeables)            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ FASE 4: ENRIQUECIMIENTO (5 segundos, background)            │
│ - Sistema carga perfil de cliente (si existe)               │
│ - Carga inteligencia de sector (cache Redis)                │
│ - Prepara contexto para generación                          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ FASE 5: GENERACIÓN (15 segundos)                            │
│ - Gemini genera propuesta con:                              │
│   * Contexto del cliente                                    │
│   * Casos seleccionados                                     │
│   * Perfil de objetivos                                     │
│   * Inteligencia de sector                                  │
│ - Output: Propuesta slide-ready (300-500 palabras)          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ FASE 6: REFINAMIENTO (5-10 minutos, opcional)               │
│ - Chat conversacional para ajustes                          │
│ - "Más corto", "Más formal", "Enfatiza X"                  │
│ - Versionado (v1, v2, v3...)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ FASE 7: EXPORTACIÓN (2 minutos)                             │
│ - Copiar texto                                              │
│ - Exportar PDF con branding NEO                             │
│ - Guardar en CRM                                            │
│ - Completar perfil de cliente (si es nuevo)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
            ✅ PROPUESTA LISTA PARA PRESENTAR
```

**Tiempo total: 20-30 minutos (vs 6 horas manual)**

---

## Valor Generado en Cada Fase

| Fase | Valor para Joven | Valor para NEO | Dato Persistido |
|------|------------------|----------------|-----------------|
| Intake | Estructura clara | Contexto de oportunidad | Sesión |
| Búsqueda | Casos relevantes al instante | Uso de base de conocimiento | Analytics |
| Curación | Control total de selección | Feedback de relevancia | Interacción |
| Enriquecimiento | Contexto automático | Perfil de cliente actualizado | Qdrant |
| Generación | Propuesta profesional en segundos | Contenido reutilizable | Historial |
| Refinamiento | Propuesta personalizada | Preferencias de tono | Perfil usuario |
| Exportación | Listo para presentar | Métrica de éxito | CRM |

---

## Diferenciadores Clave

### vs. ChatGPT Genérico
- ✅ Casos reales de NEO, no alucinaciones
- ✅ Contexto de cliente y sector integrado
- ✅ Propuestas slide-ready, no ensayos largos
- ✅ Memoria de cliente persistente

### vs. Búsqueda Manual en Drive
- ✅ Búsqueda semántica, no por palabras clave
- ✅ Ranking automático por relevancia
- ✅ Generación automática de propuesta
- ✅ 18x más rápido

### vs. Herramientas de Propuestas Genéricas
- ✅ Casos de éxito reales, no templates
- ✅ Inteligencia de sector actualizada
- ✅ Personalización por cliente
- ✅ Integración con conocimiento NEO

---

## Métricas de Éxito

### Para el Joven
- Tiempo de propuesta: < 30 minutos (vs 6 horas)
- Confianza en propuesta: > 8/10
- Tasa de uso: > 80% de oportunidades

### Para NEO
- Tasa de conversión: +15-25%
- Velocidad de respuesta a licitaciones: 24h (vs 3-5 días)
- Reutilización de casos: > 60% de propuestas
- Retención de consultores: Mejora por escalabilidad

### Para el Producto
- Uptime: > 99.5%
- Latencia búsqueda: < 2 segundos
- Latencia generación: < 15 segundos
- Satisfacción usuario: > 4.5/5

---

## Próximas Fases (Post-MVP)

1. **Integración CRM:** Guardar propuestas automáticamente
2. **Análisis de Conversión:** Trackear qué propuestas ganan
3. **Agente Autónomo:** Generar propuesta sin intervención
4. **Multiidioma:** Soporte para español, inglés, portugués
5. **Mobile App:** Acceso desde campo
6. **Integraciones:** Slack, Teams, Outlook