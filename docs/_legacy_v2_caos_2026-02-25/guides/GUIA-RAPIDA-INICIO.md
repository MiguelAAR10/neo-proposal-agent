# ⚡ GUÍA RÁPIDA DE INICIO - NEO PROPOSAL AGENT

## 5 Minutos: Entiende el Producto

### El Problema
Consultores junior tardan **6 horas** en crear propuestas comerciales.

### La Solución
Un sistema que genera propuestas en **20 minutos** usando:
- Casos de éxito reales (NEO + benchmarks)
- Perfil del cliente (objetivos, prioridades)
- Inteligencia de sector (tendencias, benchmarks)

### El Flujo
```
1. Ingresa datos (empresa, área, problema)
2. Elige switch (NEO / AI / Ambos)
3. Sistema busca casos similares
4. Selecciona casos relevantes
5. Sistema genera propuesta
6. Refina si es necesario
7. Exporta PDF

Total: 20-30 minutos
```

### El Valor
- ⏱️ 18x más rápido
- 📊 Propuestas data-driven
- 📈 +15-25% tasa de conversión
- 🚀 Escalabilidad

---

## 10 Minutos: Entiende la Arquitectura

### Stack
```
Frontend:  Next.js 14 + React 18 + Tailwind
Backend:   FastAPI + LangGraph + Qdrant + Redis
LLM:       Gemini 1.5 (embeddings + generación)
Deploy:    Docker + AWS
```

### Componentes Clave
```
┌─────────────────────────────────────────┐
│ FRONTEND (Next.js)                      │
│ Formulario → Tarjetas → Chat → Propuesta│
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│ BACKEND (FastAPI + LangGraph)           │
│ Agente: Intake → Search → Curate → Draft│
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──┐  ┌──────▼──┐  ┌─────▼──┐
│Qdrant│  │ Redis   │  │ Gemini │
│Cases │  │ Cache   │  │ LLM    │
└──────┘  └─────────┘  └────────┘
```

### Dos Colecciones Qdrant
1. **neo_cases_v1** - Casos de éxito (NEO + benchmarks)
2. **neo_profiles_v1** - Perfiles de cliente (objetivos, prioridades)

### El Switch del Usuario
```
¿Qué tipo de casos buscas?
○ Solo casos NEO (credibilidad interna)
○ Solo benchmarks AI (innovación)
● Ambos (máximo contexto)
```

---

## 15 Minutos: Entiende los Requisitos

### MVP (Sprint 1-2)
- ✅ Formulario de entrada
- ✅ Búsqueda de casos
- ✅ Visualización en tarjetas
- ✅ Selección de casos (HITL)
- ✅ Generación de propuesta
- ✅ Exportación PDF
- ✅ Gestión de perfiles

### Post-MVP (Sprint 3+)
- ⏳ Chat de refinamiento
- ⏳ Inteligencia de sector
- ⏳ Refinamiento conversacional

### Requisitos Funcionales Clave
1. **RF-01:** Switch de colección (NEO/AI/Ambos)
2. **RF-02:** Formulario inteligente con autocomplete
3. **RF-03:** Búsqueda por similitud semántica
4. **RF-04:** Visualización en tarjetas
5. **RF-06:** Generación de propuesta
6. **RF-08:** Exportación PDF
7. **RF-09:** Gestión de perfiles

---

## 20 Minutos: Entiende tu Rol

### 👨‍💼 Product Manager
**Lectura:** `01-VISION-NEGOCIO.md` + `03-JOURNEY-MAPS.md`
**Responsabilidades:**
- Definir prioridades
- Validar requisitos
- Comunicar con stakeholders
- Medir éxito

### 🏗️ Arquitecto
**Lectura:** `02-ARQUITECTURA-SISTEMA.md` + `05-REQUISITOS-TECNICOS.md`
**Responsabilidades:**
- Validar diseño técnico
- Resolver problemas de integración
- Asegurar escalabilidad
- Documentar decisiones

### 💻 Backend Expert
**Lectura:** `SKILLS-BACKEND-EXPERT.md` + `02-ARQUITECTURA-SISTEMA.md`
**Responsabilidades:**
- Implementar FastAPI
- Orquestar LangGraph
- Integrar Qdrant + Redis + Gemini
- Escribir tests
- Documentar API

**Stack:** FastAPI, LangGraph, Qdrant, Redis, Gemini

### 🎨 Frontend Expert
**Lectura:** `SKILLS-FRONTEND-UX-EXPERT.md` + `03-JOURNEY-MAPS.md`
**Responsabilidades:**
- Implementar Next.js
- Crear componentes UI
- Manejar estado con Zustand
- Integrar TanStack Query
- Optimizar performance

**Stack:** Next.js, React, Tailwind, Zustand, TanStack Query

---

## 30 Minutos: Setup Local

### Requisitos
- Docker + Docker Compose
- Node.js 20+
- Python 3.11+
- Git

### Paso 1: Clonar Repos
```bash
git clone https://github.com/neo/proposal-agent-backend.git
git clone https://github.com/neo/proposal-agent-frontend.git
```

### Paso 2: Configurar Variables de Entorno

**Backend (.env):**
```
GEMINI_API_KEY=xxx
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
ALLOWED_ORIGINS=http://localhost:3000
```

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Paso 3: Ejecutar Docker Compose
```bash
docker-compose up
```

Esto inicia:
- Qdrant (puerto 6333)
- Redis (puerto 6379)
- Backend (puerto 8000)
- Frontend (puerto 3000)

### Paso 4: Verificar Health
```bash
curl http://localhost:8000/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "qdrant": {"cases": 0, "profiles": 0},
  "redis": "connected",
  "gemini": "ok"
}
```

### Paso 5: Ingestar Datos (Opcional)
```bash
python backend/scripts/ingest_cases.py \
  --csv-ai data/benchmarks.csv \
  --csv-neo data/neo_cases.csv
```

---

## 45 Minutos: Primer Commit

### Backend
```bash
cd backend

# Crear estructura
mkdir -p app/{routers,services,graph/nodes,models}
touch app/__init__.py app/main.py app/config.py

# Instalar dependencias
pip install -r requirements.txt

# Crear primer endpoint
# (Ver SKILLS-BACKEND-EXPERT.md para código)

# Tests
pytest tests/unit/ -v

# Commit
git add .
git commit -m "feat: setup FastAPI base"
```

### Frontend
```bash
cd frontend

# Crear estructura
npx create-next-app@latest . --typescript --tailwind

# Instalar dependencias
npm install zustand @tanstack/react-query framer-motion

# Crear primer componente
# (Ver SKILLS-FRONTEND-UX-EXPERT.md para código)

# Tests
npm test

# Commit
git add .
git commit -m "feat: setup Next.js base"
```

---

## 1 Hora: Entender el Flujo Completo

### Fase 1: Entrada (30 seg)
```
Usuario abre app
↓
Ingresa: empresa, área, problema
↓
Elige switch: "Ambos"
↓
Presiona "Buscar casos"
```

**Backend:**
- Validar inputs (Pydantic)
- Crear sesión (Redis)
- Retornar thread_id

**Frontend:**
- Mostrar formulario
- Validar con Zod
- Guardar en Zustand

### Fase 2: Búsqueda (10 seg)
```
Backend recibe problema
↓
Genera embedding (Gemini)
↓
Busca en Qdrant (con filtro tipo)
↓
Retorna top 6-8 casos
```

**Backend:**
- Llamar Gemini para embedding
- Buscar en Qdrant
- Aplicar filtro según switch
- Retornar casos

**Frontend:**
- Mostrar spinner
- Recibir casos
- Mostrar en tarjetas

### Fase 3: Curación (5 min)
```
Usuario ve tarjetas
↓
Selecciona casos relevantes
↓
Presiona "Generar propuesta"
```

**Frontend:**
- Mostrar tarjetas con checkbox
- Permitir múltiple selección
- Mostrar chat panel
- Habilitar botón "Generar"

### Fase 4: Generación (15 seg)
```
Backend recibe casos seleccionados
↓
Carga perfil de cliente (si existe)
↓
Carga inteligencia de sector (cache Redis)
↓
Construye prompt
↓
Llama Gemini
↓
Retorna propuesta
```

**Backend:**
- Buscar perfil en Qdrant
- Buscar sector intel en Redis
- Construir prompt enriquecido
- Llamar Gemini
- Parsear respuesta

**Frontend:**
- Mostrar propuesta
- Mostrar toolbar (copiar, PDF, etc.)
- Habilitar chat para refinamiento

### Fase 5: Exportación (2 min)
```
Usuario presiona "Exportar PDF"
↓
Sistema genera PDF con branding
↓
Usuario descarga
```

**Frontend:**
- Generar PDF con html2pdf
- Incluir branding NEO
- Descargar

---

## 2 Horas: Primeras Tareas

### Backend
- [ ] Implementar FastAPI app con lifespan
- [ ] Configurar Pydantic Settings
- [ ] Conectar a Qdrant
- [ ] Conectar a Redis
- [ ] Integrar Gemini
- [ ] Crear endpoint `/health`
- [ ] Crear endpoint `/agent/start`
- [ ] Escribir tests

### Frontend
- [ ] Configurar Next.js 14
- [ ] Crear Zustand store
- [ ] Crear componente InitialForm
- [ ] Crear componente CaseCard
- [ ] Integrar TanStack Query
- [ ] Crear hook useSearchCases
- [ ] Escribir tests

---

## Checklist de Inicio

### Antes de Empezar
- [ ] Todos leyeron documentación según rol
- [ ] Preguntas aclaradas
- [ ] Repos creados
- [ ] Acceso a APIs (Gemini, etc.)
- [ ] Docker instalado

### Primer Día
- [ ] Clonar repos
- [ ] Instalar dependencias
- [ ] Ejecutar `docker-compose up`
- [ ] Verificar health checks
- [ ] Crear primer commit

### Primera Semana
- [ ] MVP core funcionando
- [ ] Tests básicos pasando
- [ ] Documentación actualizada
- [ ] Demo interna

---

## Documentación Rápida

| Documento | Tiempo | Para Quién |
|-----------|--------|-----------|
| `RESUMEN-EJECUTIVO.md` | 10 min | Todos |
| `01-VISION-NEGOCIO.md` | 30 min | PM, Stakeholders |
| `02-ARQUITECTURA-SISTEMA.md` | 1 hora | Arquitecto, Tech Leads |
| `03-JOURNEY-MAPS.md` | 45 min | PM, Frontend, UX |
| `04-REQUISITOS-FUNCIONALES.md` | 1 hora | Todos |
| `05-REQUISITOS-TECNICOS.md` | 1 hora | Backend, Arquitecto |
| `SKILLS-BACKEND-EXPERT.md` | 2 horas | Backend |
| `SKILLS-FRONTEND-UX-EXPERT.md` | 2 horas | Frontend |
| `00-INDEX-DOCUMENTACION.md` | 15 min | Todos (referencia) |

---

## Preguntas Frecuentes

### ¿Por dónde empiezo?
1. Lee `RESUMEN-EJECUTIVO.md` (10 min)
2. Lee documentación según tu rol (1-2 horas)
3. Haz preguntas en kickoff
4. Comienza desarrollo

### ¿Qué es el switch?
El usuario elige qué tipo de casos buscar:
- "Solo casos NEO" → Filtro: `tipo="NEO"`
- "Solo benchmarks AI" → Filtro: `tipo="AI"`
- "Ambos" → Sin filtro

### ¿Qué pasa si Qdrant está vacío?
- Health check detecta 0 casos
- Mostrar mensaje: "Base de conocimiento vacía"
- Deshabilitar búsqueda
- Endpoint admin para ingestar datos

### ¿Cómo escalo?
- Backend stateless (todo en Redis/Qdrant)
- Load balancer (ALB)
- Auto-scaling (ECS)
- Qdrant Cloud o cluster
- ElastiCache para Redis

### ¿Cuál es el MVP?
Funcionalidades críticas:
- Formulario de entrada
- Búsqueda de casos
- Visualización en tarjetas
- Selección de casos
- Generación de propuesta
- Exportación PDF
- Gestión de perfiles

---

## Contacto & Ayuda

**Documentación:** Consultar `00-INDEX-DOCUMENTACION.md`
**Preguntas técnicas:** Revisar `SKILLS-*-EXPERT.md`
**Preguntas de negocio:** Revisar `01-VISION-NEGOCIO.md`
**Preguntas de UX:** Revisar `03-JOURNEY-MAPS.md`

---

## Próximos Pasos

1. ✅ Leer esta guía (5 min)
2. ⏳ Leer documentación según rol (1-2 horas)
3. ⏳ Hacer preguntas en kickoff
4. ⏳ Clonar repos y setup local
5. ⏳ Crear primer commit
6. ⏳ Comenzar desarrollo

---

**¡Listo para empezar!** 🚀

Cualquier pregunta, consulta la documentación completa o pregunta en el kickoff.