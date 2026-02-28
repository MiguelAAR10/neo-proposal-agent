# 02 - ARQUITECTURA DEL SISTEMA

## Diagrama de Componentes (Alto Nivel)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js/React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Formulario  │  │  Tarjetas    │  │  Chat de Refinamiento    │  │
│  │  Inicial     │  │  Casos       │  │  + Propuesta             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/WebSocket
┌────────────────────────────▼────────────────────────────────────────┐
│                    BACKEND (FastAPI)                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  LangGraph Agent Orchestrator                                  │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │ │
│  │  │ Intake   │ │ Search   │ │ Curate   │ │ Draft/Refine     │  │ │
│  │  │ Node     │ │ Node     │ │ (HITL)   │ │ Node             │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Case Tool    │  │ Profile Tool │  │ Sector Tool              │  │
│  │ (Qdrant)     │  │ (Qdrant)     │  │ (Redis + Gemini)         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼──────┐  ┌──────────▼────────┐  ┌──────▼──────┐
│   Qdrant     │  │     Redis         │  │   Gemini    │
│  (Vector DB) │  │    (Cache)        │  │   (LLM)     │
│              │  │                   │  │             │
│ neo_cases_v1 │  │ Sector intel      │  │ Embeddings  │
│neo_profiles_v1│ │ frecuentes        │  │ Generation  │
└──────────────┘  └───────────────────┘  └─────────────┘
```

---

## Stack Tecnológico

| Capa | Tecnología | Versión | Justificación |
|------|-----------|---------|---------------|
| **Frontend** | Next.js | 16+ | SSR, SEO, componentes reutilizables |
| **Frontend** | React | 19+ | Componentes, hooks, estado |
| **Frontend** | Tailwind CSS | 3.4+ | Estilos rápidos, responsive |
| **Frontend** | Zustand | Latest | Estado global ligero |
| **Frontend** | TanStack Query | 5+ | Data fetching, caching |
| **Backend** | FastAPI | 0.110+ | Async nativo, validación Pydantic |
| **Agente** | LangGraph | 0.1+ | Ciclos, memoria, HITL |
| **Vector DB** | Qdrant | 1.9+ | Self-hostable, filtrado payload |
| **Cache** | Redis | 7+ | Sector intel, sesiones |
| **LLM** | Gemini 2.0 Flash/Pro | Latest | Embeddings 768d, costo-efectivo |
| **Deploy** | Docker | Latest | Contenerización |
| **Orquestación** | Docker Compose | Latest | MVP local |

---

## Colecciones Qdrant: Especificación Detallada

### Colección 1: `neo_cases_v1`

**Propósito:** Almacenar casos de éxito (NEO + benchmarks externos)

**Configuración:**
```
Nombre: neo_cases_v1
Dimensión vectores: 768 (modelo gemini-embedding-001)
Distancia: Cosine
Tamaño esperado: 500-1000 puntos (MVP)
```

**Payload Schema:**
```json
{
  "id": "string",                    // BENCH-001, NEO-042
  "tipo": "enum",                    // "AI" | "NEO"
  "origen_detectado": "string",      // "BENCH" | "NEO"
  "titulo": "string",                // KPI llamativo (max 100 chars)
  "empresa": "string",               // Cliente o referencia
  "industria": "string",             // Banca, Retail, Tech, etc.
  "area": "string",                  // Marketing, Ops, TI, Ventas, RRHH
  "problema": "string",              // Descripción del dolor (max 500 chars)
  "solucion": "string",              // Qué se hizo (max 500 chars)
  "beneficios": ["string"],          // Lista de beneficios cuantitativos
  "tecnologias": ["string"],         // LLMs, Computer Vision, RPA, etc.
  "kpi_impacto": "string",           // "30% reducción costos"
  "url_slide": "string",             // URL clickeable al PDF/Drive
  "contexto_embedding": "string",    // Texto para vectorizar (CURADO)
  "nivel_enriquecimiento": "string", // "alto" | "medio" | "bajo"
  "fecha_ingesta": "date"            // Cuándo se agregó
}
```

**Payload Indexes (para performance):**
```
- tipo: keyword (filtro principal)
- industria: keyword (enriquecimiento)
- area: keyword (enriquecimiento)
- origen_detectado: keyword (analytics)
```

**Ejemplo de punto:**
```json
{
  "id": "BENCH-001",
  "tipo": "AI",
  "origen_detectado": "BENCH",
  "titulo": "Automatización de reportes: 40% reducción",
  "empresa": "Referencia externa",
  "industria": "Banca",
  "area": "Operaciones",
  "problema": "Equipo de 5 analistas dedica 60% del tiempo a reportes manuales en Excel",
  "solucion": "Agentes IA para validación y generación automática de reportes",
  "beneficios": ["40% reducción en tiempo", "0 errores manuales", "Escalable a 10x volumen"],
  "tecnologias": ["LLMs", "Python", "Power BI", "RPA"],
  "kpi_impacto": "40% reducción en 3 meses",
  "url_slide": "https://drive.google.com/file/d/...",
  "contexto_embedding": "Automatización de reportes financieros. Problema: procesamiento manual lento. Solución: agentes IA. Impacto: 40% reducción.",
  "nivel_enriquecimiento": "alto",
  "fecha_ingesta": "2024-02-20"
}
```

---

### Colección 2: `neo_profiles_v1`

**Propósito:** Memoria de objetivos por empresa y área

**Configuración:**
```
Nombre: neo_profiles_v1
Dimensión vectores: 768 (modelo gemini-embedding-001)
Distancia: Cosine
Tamaño esperado: 100-300 puntos (MVP)
```

**Payload Schema:**
```json
{
  "id": "string",                    // "TechCorp-Marketing"
  "empresa": "string",               // "TechCorp"
  "area": "string",                  // "Marketing Digital"
  "industria": "string",             // "Tecnología"
  "objetivos": ["string"],           // ["Automatizar 30%", "Reducir churn"]
  "prioridades": ["string"],         // Ordenadas por importancia
  "dolor_principal": "string",       // Problema crítico actual
  "presupuesto_estimado": "string",  // "Alto", "Medio", "Bajo"
  "decisor": "string",               // Quién toma la decisión
  "ciclo_compra": "string",          // "Largo", "Medio", "Corto"
  "notas_adicionales": "string",     // Contexto libre
  "ultima_actualizacion": "date",    // Para staleness
  "creado_por": "string"             // Email del consultor
}
```

**Payload Indexes:**
```
- empresa: keyword (búsqueda)
- area: keyword (búsqueda)
- industria: keyword (enriquecimiento)
```

**Ejemplo de punto:**
```json
{
  "id": "TechCorp-Marketing",
  "empresa": "TechCorp",
  "area": "Marketing Digital",
  "industria": "Tecnología",
  "objetivos": [
    "Automatizar reportes en 30%",
    "Reducir churn de clientes 15%",
    "Aumentar leads calificados 40%"
  ],
  "prioridades": [
    "Automatización",
    "Data-driven decisions",
    "Personalización a escala"
  ],
  "dolor_principal": "Equipos dedican 60% del tiempo a reportes manuales",
  "presupuesto_estimado": "Medio-Alto",
  "decisor": "CMO y VP de Digital",
  "ciclo_compra": "Medio (3-6 meses)",
  "notas_adicionales": "Prefieren soluciones cloud-native, presupuesto aprobado",
  "ultima_actualizacion": "2024-02-15",
  "creado_por": "consultor@neo.com"
}
```

---

## El Switch del Usuario: Activación de Colecciones

El consultor elige al inicio qué colección de casos activar. Esto determina el filtro en la búsqueda:

### Opciones del Switch

| Switch | Filtro Qdrant | Descripción | Caso de Uso |
|--------|---------------|-------------|-----------|
| **"Solo casos NEO"** | `tipo="NEO"` | Proyectos históricos de NEO | Cuando quiero máxima credibilidad interna |
| **"Solo benchmarks AI"** | `tipo="AI"` | Casos externos, inspiración | Cuando quiero innovación y referencias externas |
| **"Ambos"** (default) | Sin filtro tipo | Híbrido, máximo contexto | Cuando quiero máxima cobertura |

### Implementación del Switch

**En Frontend:**
```
┌─────────────────────────────────┐
│ ¿Qué tipo de casos buscas?      │
│                                 │
│ ○ Solo casos NEO                │
│ ○ Solo benchmarks AI            │
│ ● Ambos (recomendado)           │
│                                 │
│ [Buscar casos →]                │
└─────────────────────────────────┘
```

**En Backend (LangGraph):**
```python
# En el nodo de búsqueda
def search_node(state: ProposalState) -> ProposalState:
    switch_value = state.get("switch")  # "neo", "ai", "both"
    
    # Construir filtro
    if switch_value == "neo":
        filter = Filter(must=[FieldCondition(key="tipo", match=MatchValue(value="NEO"))])
    elif switch_value == "ai":
        filter = Filter(must=[FieldCondition(key="tipo", match=MatchValue(value="AI"))])
    else:  # "both"
        filter = None
    
    # Buscar en Qdrant
    results = qdrant_client.search(
        collection_name="neo_cases_v1",
        query_vector=embedding,
        query_filter=filter,
        limit=6
    )
    
    return {**state, "cases": results}
```

---

## Manejo de Qdrant Vacío (Reinicio)

**Escenario:** Se reinicia Qdrant o es la primera vez que se ejecuta.

**Comportamiento esperado:**

1. **Detección:**
   ```python
   def check_qdrant_health():
       try:
           collections = qdrant_client.get_collections()
           case_count = qdrant_client.count("neo_cases_v1").count
           profile_count = qdrant_client.count("neo_profiles_v1").count
           
           if case_count == 0:
               return {"status": "empty", "message": "No hay casos disponibles"}
           return {"status": "ok", "cases": case_count, "profiles": profile_count}
       except Exception as e:
           return {"status": "error", "message": str(e)}
   ```

2. **Respuesta en Frontend:**
   ```
   ⚠️ Base de conocimiento vacía
   
   No hay casos disponibles en el sistema.
   
   Contacta a admin@neo.com para ingestar datos.
   
   [Reintentar]
   ```

3. **Endpoint de Health Check:**
   ```
   GET /health
   
   Response:
   {
     "status": "ok" | "empty" | "error",
     "qdrant": {"cases": 500, "profiles": 150},
     "redis": "connected",
     "gemini": "ok"
   }
   ```

---

## Redis: Estrategia de Cache

### Propósito
Cachear datos que no cambian frecuentemente (inteligencia de sector, datos de industria) para evitar llamadas repetidas a Gemini.

### Claves y TTL

| Patrón de Clave | Contenido | TTL | Justificación |
|-----------------|-----------|-----|---------------|
| `sector:{rubro}:{area}` | JSON inteligencia sector | 30 días | Sector no cambia rápido |
| `sector:{rubro}:general` | JSON inteligencia general rubro | 30 días | Fallback cuando no hay área |
| `search:{hash_query}` | Resultados búsqueda casos | 1 hora | Evita recomputar embeddings |
| `session:{session_id}` | Estado del grafo LangGraph | 24 horas | Persistencia conversación |
| `frecuentes:rubros` | Lista rubros más consultados | 7 días | Analytics, warm cache |

### Ejemplo de Dato en Cache

```json
// Clave: sector:Banca:Operaciones
{
  "rubro": "Banca",
  "area": "Operaciones",
  "generated_at": "2024-02-20T10:00:00Z",
  "fuente": "gemini_web_grounding",
  
  "tendencias_clave": [
    "Automatización de procesos con RPA",
    "Detección de fraude con ML",
    "Compliance automático con IA"
  ],
  
  "benchmarks_digitales": {
    "reduccion_tiempo_reportes": "30-40% típico",
    "mejora_deteccion_fraude": "15-25% vs manual",
    "roi_automatizacion": "5:1 promedio en 12 meses"
  },
  
  "oportunidades_ia": [
    "Agentes para validación de transacciones",
    "Generación automática de reportes regulatorios",
    "Optimización de flujos de aprobación"
  ]
}
```

### Invalidación de Cache

**Manual (Admin):**
```
POST /admin/cache/invalidate?pattern=sector:*
```

**Automática:**
- TTL expira automáticamente
- Regeneración transparente en próximo request

---

## Flujo de Datos: De Ingesta a Propuesta

### 1. Ingesta Inicial (CLI/Admin)

```
CSV (AI) + CSV (NEO)
    ↓
Python script (ingest_cases.py)
    ↓
Normalización a schema unificado
    ↓
Generación de embeddings (Gemini)
    ↓
Upsert a Qdrant (neo_cases_v1)
    ↓
✅ Casos disponibles para búsqueda
```

### 2. Consulta de Casos (Runtime)

```
Problema del usuario
    ↓
Embedding (Gemini)
    ↓
Búsqueda Qdrant (con filtro tipo según switch)
    ↓
Ranking por score coseno
    ↓
Retornar top 6-8 casos
    ↓
Mostrar en tarjetas
```

### 3. Enriquecimiento (Runtime)

```
Empresa + Área
    ↓
Búsqueda en Qdrant (neo_profiles_v1)
    ↓
¿Existe perfil?
    ├─ SÍ → Usar perfil
    └─ NO → Buscar en Redis cache sector
           ├─ HIT → Usar cache
           └─ MISS → Llamar Gemini + Web
                     ↓
                     Guardar en Redis (TTL 30 días)
```

### 4. Generación de Propuesta (Runtime)

```
Casos seleccionados + Perfil + Sector
    ↓
Construir prompt enriquecido
    ↓
Llamar Gemini (temperatura 0.3)
    ↓
Parsear respuesta
    ↓
Retornar propuesta slide-ready
```

---

## Escalabilidad: MVP → Producción

| Aspecto | MVP | Producción |
|---------|-----|------------|
| **Qdrant** | Docker local | Qdrant Cloud o ECS cluster |
| **Redis** | Docker local | ElastiCache Redis |
| **Backend** | Single container | Auto-scaling ECS con ALB |
| **Frontend** | Vercel | CloudFront + S3 o Vercel Pro |
| **Gemini** | API directa | Con rate limiting, fallback |
| **Observabilidad** | Logs stdout | LangSmith + Datadog |
| **Base de datos** | Qdrant + Redis | Qdrant Cloud + ElastiCache |

---

## Seguridad Básica

| Aspecto | Implementación |
|--------|----------------|
| **API Keys** | Header `X-API-Key` para endpoints admin |
| **CORS** | Orígenes explícitos, no wildcard |
| **Rate Limiting** | 100 req/min por IP |
| **Validación** | Pydantic en todos los inputs |
| **Secrets** | Variables de entorno, no hardcodeadas |

---

## Monitoreo y Observabilidad

| Métrica | Herramienta | Umbral |
|---------|-----------|--------|
| **Uptime** | Healthcheck | > 99.5% |
| **Latencia búsqueda** | Logs | < 2 segundos |
| **Latencia generación** | Logs | < 15 segundos |
| **Errores Gemini** | LangSmith | < 1% |
| **Cache hit rate** | Redis | > 70% |
| **Satisfacción usuario** | Feedback | > 4.5/5 |
