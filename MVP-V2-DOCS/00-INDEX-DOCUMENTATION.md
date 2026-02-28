# 📚 ÍNDICE DE DOCUMENTACIÓN - NEO PROPOSAL AGENT

> Estado actualizado de esta documentación: **2026-02-28**

## Estructura de Carpetas

```
neo-proposal-agent-docs/
├── 00-INDEX-DOCUMENTACION.md          ← Estás aquí
├── BITACORA_MVP_V2.md                 ← Estado real, decisiones y aprendizajes
├── MVP-2.1-ARQUITECTURA-Y-LOGICA.md   ← Documento rector de ejecucion MVP 2.1
│
├── REQUIREMENTS/ (Lógica del Proyecto)
│   ├── 01-VISION-NEGOCIO.md
│   ├── 02-ARQUITECTURA-SISTEMA.md
│   ├── 03-JOURNEY-MAPS.md
│   ├── 04-REQUISITOS-FUNCIONALES.md
│   └── 05-REQUISITOS-TECNICOS.md
│
└── SKILLS/ (Perfiles de Expertos)
    ├── SKILLS-BACKEND-EXPERT.md
    └── SKILLS-FRONTEND-UX-EXPERT.md
```

---

## ⚠️ Estado Real de Implementación (MVP V2)

Este índice resume objetivos y diseño, pero la fuente de verdad del avance real está en `BITACORA_MVP_V2.md`.

Resumen rápido:

* Backend V2 operativo en endpoints `/agent/start`, `/agent/{thread_id}/select`, `/agent/{thread_id}/state`.
* Frontend principal V2: `frontend-web/` (Next.js).
* `frontend/app.py` (Streamlit) es legado de V1 y no está alineado al contrato API actual de V2.
* Brecha activa: chat de Next.js sigue mockeado y falta endpoint de chat productivo.
* Plan de reconstruccion tecnica: `MVP-2.1-ARQUITECTURA-Y-LOGICA.md`.

---

## 📖 Guía de Lectura por Rol

**Lectura base obligatoria para cualquier rol:** `BITACORA_MVP_V2.md` (estado real, decisiones y deuda activa).
**Lectura obligatoria para ejecucion actual:** `MVP-2.1-ARQUITECTURA-Y-LOGICA.md`.

### 👨‍💼 Product Manager / Stakeholder

**Lectura recomendada (30 minutos):**

1. `01-VISION-NEGOCIO.md` - Entiende el problema y valor

2. `03-JOURNEY-MAPS.md` - Visualiza el flujo del usuario

3. `04-REQUISITOS-FUNCIONALES.md` - Qué debe hacer el sistema

**Preguntas que responde:**

* ¿Cuál es el problema que resolvemos?

* ¿Cuál es el valor para el usuario?

* ¿Cómo se ve la experiencia del usuario?

* ¿Qué funcionalidades son críticas?

---

### 🏗️ Arquitecto de Soluciones

**Lectura recomendada (1 hora):**

1. `01-VISION-NEGOCIO.md` - Contexto

2. `02-ARQUITECTURA-SISTEMA.md` - Diseño técnico completo

3. `05-REQUISITOS-TECNICOS.md` - Stack y especificaciones

4. `03-JOURNEY-MAPS.md` - Flujos de datos

**Preguntas que responde:**

* ¿Cómo está estructurado el sistema?

* ¿Qué tecnologías se usan y por qué?

* ¿Cómo escala?

* ¿Cuáles son los puntos críticos?

---

### 💻 Backend Expert (FastAPI + LangGraph)

**Lectura recomendada (2 horas):**

1. `01-VISION-NEGOCIO.md` - Contexto de negocio

2. `02-ARQUITECTURA-SISTEMA.md` - Diseño del backend

3. `05-REQUISITOS-TECNICOS.md` - Especificaciones técnicas

4. `SKILLS-BACKEND-EXPERT.md` - Patrones de implementación

5. `04-REQUISITOS-FUNCIONALES.md` - Requisitos funcionales

**Preguntas que responde:**

* ¿Cómo implemento el agente con LangGraph?

* ¿Cómo integro Qdrant y Redis?

* ¿Cómo manejo errores y fallbacks?

* ¿Cuáles son los patrones de código esperados?

**Tareas principales:**

* \[ \] Implementar FastAPI app con lifespan

* \[ \] Diseñar e implementar LangGraph agent

* \[ \] Integrar Qdrant para búsqueda

* \[ \] Implementar Redis para caching

* \[ \] Integrar Gemini para embeddings y generación

* \[ \] Implementar endpoints de API

* \[ \] Escribir tests

* \[ \] Documentar API con OpenAPI

---

### 🎨 Frontend/UX Expert (Next.js + React)

**Lectura recomendada (2 horas):**

1. `01-VISION-NEGOCIO.md` - Contexto de negocio

2. `03-JOURNEY-MAPS.md` - Flujos del usuario

3. `04-REQUISITOS-FUNCIONALES.md` - Requisitos funcionales

4. `SKILLS-FRONTEND-UX-EXPERT.md` - Patrones de implementación

5. `02-ARQUITECTURA-SISTEMA.md` - Integración con backend

**Preguntas que responde:**

* ¿Cómo estructuro la aplicación Next.js?

* ¿Cómo manejo el estado global con Zustand?

* ¿Cómo integro TanStack Query?

* ¿Cuáles son los componentes principales?

* ¿Cómo implemento animaciones?

**Tareas principales:**

* \[ \] Configurar Next.js 14 con App Router

* \[ \] Implementar Zustand stores

* \[ \] Crear componentes de UI

* \[ \] Implementar formularios con React Hook Form

* \[ \] Integrar TanStack Query

* \[ \] Implementar chat panel

* \[ \] Agregar animaciones con Framer Motion

* \[ \] Optimizar performance

* \[ \] Escribir tests

---

## 🎯 Flujo de Lectura Recomendado (Equipo Completo)

### Semana 1: Alineación

**Lunes (Kickoff):**

* Todos leen: `01-VISION-NEGOCIO.md` (30 min)

* Discusión: ¿Entendemos el problema? ¿El valor?

**Martes (Arquitectura):**

* Todos leen: `02-ARQUITECTURA-SISTEMA.md` (1 hora)

* Discusión: ¿Preguntas sobre el diseño?

**Miércoles (Flujos):**

* Todos leen: `03-JOURNEY-MAPS.md` (45 min)

* Discusión: ¿Cómo se ve la experiencia?

**Jueves (Requisitos):**

* Todos leen: `04-REQUISITOS-FUNCIONALES.md` (1 hora)

* Discusión: ¿Qué es MVP vs Post-MVP?

**Viernes (Técnico):**

* Backend lee: `SKILLS-BACKEND-EXPERT.md` (1.5 horas)

* Frontend lee: `SKILLS-FRONTEND-UX-EXPERT.md` (1.5 horas)

* Discusión: ¿Preguntas sobre implementación?

### Semana 2+: Desarrollo

* Backend comienza con `SKILLS-BACKEND-EXPERT.md`

* Frontend comienza con `SKILLS-FRONTEND-UX-EXPERT.md`

* Ambos consultan `02-ARQUITECTURA-SISTEMA.md` según sea necesario

---

## 📋 Resumen Ejecutivo

### El Producto

**NEO Proposal Agent** es una herramienta que acelera la creación de propuestas comerciales de consultoría, permitiendo que consultores junior generen propuestas de impacto en **20 minutos** en lugar de 6 horas.

### El Problema

* Consultores junior tardan 4-6 horas en crear propuestas

* No hay acceso sistemático a casos previos

* Propuestas carecen de contexto sectorial

* Pérdida de conocimiento institucional

### La Solución

Un sistema que triangula:

1. **Casos de éxito** (NEO + benchmarks externos)

2. **Perfiles de cliente** (memoria de objetivos)

3. **Inteligencia de sector** (tendencias, benchmarks)

### El Valor

* ⏱️ **Velocidad:** 6 horas → 20 minutos (18x más rápido)

* 📊 **Calidad:** Propuestas data-driven con casos comprobados

* 📈 **Conversión:** +15-25% tasa de cierre

* 🚀 **Escalabilidad:** Consultores junior producen como senior

### El Usuario

**"El Joven"** - Consultor junior del equipo de clientes NEO

* Bajo presión de tiempo

* Necesita generar propuestas rápidas sin perder calidad

* Quiere inspiración de casos previos

### El Flujo

```
1. Ingresa datos (empresa, área, problema)     [30 seg]
2. Elige switch (NEO / AI / Ambos)             [10 seg]
3. Sistema busca casos similares               [10 seg]
4. Selecciona casos relevantes                 [5 min]
5. Sistema genera propuesta                    [15 seg]
6. Refina si es necesario (opcional)           [5 min]
7. Exporta PDF                                 [2 min]
                                               ─────────
                                    TOTAL:     20-30 min
```

### El Stack

**Backend:**

* FastAPI (async, validación)

* LangGraph (orquestación de agente)

* Qdrant (búsqueda vectorial)

* Redis (caching)

* Gemini (embeddings + generación)

**Frontend:**

* Next.js 16 (SSR, SEO)

* React 19 (componentes)

* Tailwind CSS (estilos)

* Zustand (estado global)

* TanStack Query (data fetching)

**Infraestructura:**

* Docker (contenerización)

* Vercel (frontend)

* AWS ECS (backend)

---

## 🔑 Conceptos Clave

### Switch de Colección

El usuario elige qué tipo de casos buscar:

* **"Solo casos NEO"** → Proyectos históricos (máxima credibilidad)

* **"Solo benchmarks AI"** → Casos externos (innovación)

* **"Ambos"** → Híbrido (máximo contexto)

### HITL (Human-in-the-Loop)

El sistema sugiere, el usuario decide:

* Sistema busca casos automáticamente

* Usuario selecciona cuáles usar

* Sistema genera propuesta

* Usuario refina si es necesario

### Dos Colecciones Qdrant

1. **neo_cases_v1** - Casos de éxito (NEO + benchmarks)

2. **neo_profiles_v1** - Memoria de clientes (objetivos, prioridades)

### Tres Fuentes de Inteligencia

1. **Casos** - Búsqueda semántica en Qdrant

2. **Perfil** - Memoria de objetivos del cliente

3. **Sector** - Tendencias e inteligencia de industria (cache Redis)

---

## 📊 Matriz de Requisitos

### MVP (Sprint 1-2)

**Funcionalidades críticas:**

* ✅ Formulario de entrada

* ✅ Búsqueda de casos por similitud

* ✅ Visualización en tarjetas

* ✅ Selección de casos (HITL)

* ✅ Generación de propuesta

* ✅ Exportación PDF

* ✅ Gestión de perfiles

**No incluye:**

* ❌ Chat de refinamiento

* ❌ Inteligencia de sector

* ❌ Refinamiento conversacional

### Post-MVP (Sprint 3+)

**Funcionalidades adicionales:**

* ✅ Chat de contexto

* ✅ Refinamiento conversacional

* ✅ Inteligencia de sector

* ✅ Rate limiting

* ✅ Feedback del usuario

* ✅ Integración CRM

* ✅ Análisis de conversión

---

## 🚀 Hitos de Desarrollo

### Semana 1-2: Setup & MVP Core

* \[ \] Configurar repos (backend + frontend)

* \[ \] Setup Docker Compose

* \[ \] Implementar FastAPI base

* \[ \] Implementar Next.js base

* \[ \] Integrar Qdrant

* \[ \] Integrar Redis

* \[ \] Integrar Gemini

### Semana 3-4: Agente & Búsqueda

* \[ \] Implementar LangGraph agent

* \[ \] Implementar nodo de búsqueda

* \[ \] Implementar nodo de curación (HITL)

* \[ \] Implementar nodo de generación

* \[ \] Crear endpoints de API

* \[ \] Crear componentes de UI

### Semana 5-6: Propuesta & Exportación

* \[ \] Implementar generación de propuesta

* \[ \] Implementar exportación PDF

* \[ \] Implementar gestión de perfiles

* \[ \] Crear formulario de perfil

* \[ \] Testing completo

* \[ \] Documentación

### Semana 7+: Polish & Post-MVP

* \[ \] Chat de refinamiento

* \[ \] Inteligencia de sector

* \[ \] Rate limiting

* \[ \] Feedback del usuario

* \[ \] Performance optimization

* \[ \] Deployment a producción

---

## 📞 Preguntas Frecuentes

### ¿Por qué Qdrant y no Pinecone?

* Self-hostable (control total)

* Filtrado de payload (tipo, industria, área)

* Mejor para MVP local

* Escalable a producción

### ¿Por qué LangGraph y no LangChain?

* Mejor para ciclos y memoria

* Interrupts para HITL

* Checkpointing con Redis

* Más control sobre el flujo

### ¿Por qué Gemini y no OpenAI?

* Embeddings 768d (suficiente)

* Web grounding (inteligencia de sector)

* Costo-efectivo

* Fallback a otros modelos posible

### ¿Cómo manejo Qdrant vacío?

* Detectar en health check

* Mostrar mensaje claro

* Deshabilitar búsqueda

* Endpoint admin para ingestar datos

### ¿Cómo escalo a múltiples usuarios?

* Backend stateless (todo en Redis/Qdrant)

* Load balancer (ALB)

* Auto-scaling (ECS)

* Qdrant Cloud o cluster

* ElastiCache para Redis

---

## 📚 Referencias Externas

* [FastAPI Docs](https://fastapi.tiangolo.com/)

* [LangGraph Docs](https://langchain-ai.github.io/langgraph/)

* [Qdrant Docs](https://qdrant.tech/documentation/)

* [Next.js Docs](https://nextjs.org/docs)

* [Tailwind CSS Docs](https://tailwindcss.com/docs)

* [Zustand Docs](https://github.com/pmndrs/zustand)

* [TanStack Query Docs](https://tanstack.com/query/latest)

---

## ✅ Checklist de Inicio

### Antes de Empezar

* \[ \] Todos leyeron `01-VISION-NEGOCIO.md`

* \[ \] Todos leyeron `02-ARQUITECTURA-SISTEMA.md`

* \[ \] Backend leyó `SKILLS-BACKEND-EXPERT.md`

* \[ \] Frontend leyó `SKILLS-FRONTEND-UX-EXPERT.md`

* \[ \] Preguntas aclaradas en kickoff

* \[ \] Repos creados (backend + frontend)

* \[ \] Acceso a APIs (Gemini, etc.)

* \[ \] Docker instalado localmente

### Primer Día

* \[ \] Clonar repos

* \[ \] Instalar dependencias

* \[ \] Ejecutar `docker-compose up`

* \[ \] Verificar health checks

* \[ \] Crear primer commit

* \[ \] Configurar CI/CD

### Primera Semana

* \[ \] MVP core funcionando

* \[ \] Tests básicos pasando

* \[ \] Documentación actualizada

* \[ \] Demo interna

---

## 📝 Notas Importantes

### Principios de Diseño

1. **Tecnología es transversal** - No filtrar por stack, buscar por similitud

2. **Área es mínima** - Contexto, no filtro restrictivo

3. **HITL siempre** - Usuario decide, sistema asiste

4. **Output slide-ready** - Breve, impactante, presentable

5. **Memoria institucional** - Cada interacción enriquece el sistema

### Decisiones Críticas

1. **Switch de colección** - Permite elegir entre NEO/AI/Ambos

2. **Qdrant vacío** - Detectar y manejar gracefully

3. **Redis cache** - Sector intel con TTL 30 días

4. **Gemini con retry** - Exponential backoff para rate limiting

5. **LangGraph con interrupt** - HITL antes de curación

### Riesgos Mitigados

1. **Qdrant sin datos** → Health check + mensaje claro

2. **Gemini rate limit** → Retry exponencial + fallback

3. **Redis caído** → Graceful degradation

4. **Propuesta mala** → Refinamiento conversacional

5. **Escalabilidad** → Arquitectura stateless desde el inicio

---

## 🎓 Próximos Pasos

1. **Leer documentación** según tu rol

2. **Hacer preguntas** en kickoff

3. **Clonar repos** y setup local

4. **Comenzar desarrollo** según hitos

5. **Mantener documentación actualizada**

---

**Última actualización:** Febrero 2024\
**Versión:** 1.0 (MVP)\
**Estado:** Listo para desarrollo
