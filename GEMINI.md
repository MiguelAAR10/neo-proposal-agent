# NEO Proposal Agent V2 - Master AI Context (GEMINI.md)

Este documento es la única fuente de verdad y contexto fundacional para cualquier agente de IA (Gemini, Claude, Cursor, Windsurf, etc.) que trabaje en el proyecto **NEO Proposal Agent V2**. 

Tu objetivo principal como agente de IA es asegurar una arquitectura **Backend-First**, robusta, escalable y tolerante a fallos, construida con **FastAPI** y **LangGraph**, mientras el Frontend sigue siendo una interfaz limpia ("Dumb UI") que se construirá en **Next.js** o se mantendrá temporalmente en **Streamlit**.

---

## 1. Reglas No Negociables (Anti-patrones a evitar)
Basados en la "Bitácora de Aprendizajes V1", **JAMÁS** cometas los siguientes errores:

- ❌ **Lógica en el Frontend**: No pongas llamadas a la base de datos (Qdrant), a modelos (Gemini), ni lógicas de LangGraph en el código del Frontend (e.g., `app.py`). El Frontend SOLO envía requests HTTP y renderiza la UI.
- ❌ **Conexiones Globales y Dependencias Circulares**: No inicialices clientes (`QdrantClient`, `genai.Client`) a nivel global en el módulo. 
  - ✅ **Debes usar el patrón `lifespan`** de FastAPI en `main.py` para cargar los clientes al arrancar el servidor.
- ❌ **Variables Quemadas (Hardcoded)**: No escribas URLs, API Keys o nombres de modelos (`gemini-embedding-001`) directamente en el código lógico.
  - ✅ **Debes centralizarlas** mediante Pydantic Settings (`src/config.py`) usando el archivo `.env`.
- ❌ **Índices Faltantes en la BD Vectorial**: Qdrant requiere **Payload Indexes** (índices `KEYWORD`) para los metadatos antes de poder hacer filtrado semántico (ej. por `industria`, `area_funcional`). 
  - ✅ Siempre asegúrate de que el script de carga de datos crea la colección y añade los índices.

---

## 2. Arquitectura de la Versión 2 (MVP2)
El repositorio se divide estrictamente en `backend` y `frontend`.

### 2.1 Backend (Python 3.11+, FastAPI)
- **Punto de Entrada**: `backend/src/api/main.py`.
- **Frameworks Clave**: FastAPI, Pydantic v2, LangGraph, `qdrant-client`, `google-genai`.
- **Patrones**: 
  - Estado persistente y memoria del agente manejado mediante `thread_id` en `LangGraph` (con `MemorySaver`).
  - Nodos del agente desacoplados en `backend/src/agent/`.
  - Rutas de la API expuestas y estructuradas (ej: `POST /search`, `POST /chat`).
- **Comando de Inicio**: `cd backend && uvicorn src.api.main:app --reload --port 8000`.

### 2.2 Frontend (Streamlit para Pruebas / Next.js para Prod)
- Actualmente existe un UI base en `frontend/app.py` que consume el backend.
- **Próximos Pasos**: Migración a un framework web (Next.js/React + Tailwind) que consumirá el API del backend en el puerto `8000`.

---

## 3. Lógica del Negocio (NEO Assistant)
El sistema automatiza el descubrimiento de casos de éxito y la ideación de propuestas de valor para consultores comerciales:
1. **Intake / Search**: Se recibe la necesidad del cliente y se filtra/busca semánticamente en `Qdrant` mediante embeddings de Google (`gemini-embedding-001`).
2. **Retrieve**: Se listan los mejores `N` casos (legacy projects) que respondan al problema.
3. **Chat RAG (Human-in-the-loop)**: El consultor dialoga con el "NEO Assistant" sobre los casos encontrados para extraer ideas o redactar la propuesta usando `gemini-2.0-flash`. LangGraph persiste el historial para mantener coherencia.

---

## 4. Directorios de Referencia para el Agente
Si necesitas mayor profundidad en algún requerimiento, consulta estrictamente estas carpetas:

- 📂 `mvp-v1-memoria-fundacional/`: Contiene los detalles históricos, bitácoras de errores (muy útil para debuggear) y el Baseline de la V1.
- 📂 `neo-proposal-specs/`: (Si existe) Especificaciones de arquitectura de V2, journeys de usuario y requisitos funcionales y técnicos.

---

*Nota para el Agente: Lee, comprende y asimila estas instrucciones antes de realizar modificaciones arquitectónicas o escribir código nuevo en este repositorio.*