# NEO Proposal Agent V2 - Master AI Context

Este documento es la única fuente de verdad y contexto fundacional para CUALQUIER agente de IA (Gemini, Claude, Cursor, Windsurf, Cline, Aider, etc.) que trabaje en el proyecto **NEO Proposal Agent V2**.

Tu objetivo principal como agente de IA es asegurar una arquitectura **Backend-First**, robusta, escalable y tolerante a fallos, construida con **FastAPI** y **LangGraph**, mientras el Frontend sigue siendo una interfaz limpia ("Dumb UI").

---

## 1. Reglas No Negociables (Anti-patrones a evitar)
Basados en la "Bitácora de Aprendizajes V1", **JAMÁS** cometas los siguientes errores:

- ❌ **Lógica en el Frontend**: No pongas llamadas a la base de datos (Qdrant), a modelos (Gemini), ni lógicas de LangGraph en el código del Frontend (e.g., `frontend/app.py`). El Frontend SOLO envía requests HTTP y renderiza la UI.
- ❌ **Conexiones Globales y Dependencias Circulares**: No inicialices clientes (`QdrantClient`, `genai.Client`) a nivel global en el módulo. 
  - ✅ **Debes usar el patrón `lifespan`** de FastAPI en `main.py` para cargar los clientes al arrancar el servidor.
- ❌ **Variables Quemadas (Hardcoded)**: No escribas URLs, API Keys o nombres de modelos directamente en el código lógico.
  - ✅ **Debes centralizarlas** mediante Pydantic Settings (`backend/src/config.py`) usando el archivo `.env`.
- ❌ **Índices Faltantes en la BD Vectorial**: Qdrant requiere **Payload Indexes** (índices `KEYWORD`) para los metadatos antes de poder hacer filtrado semántico. 
  - ✅ Siempre asegúrate de que el script de carga de datos crea la colección y añade los índices.

---

## 2. Arquitectura de la Versión 2 (MVP2)
El repositorio se divide estrictamente en `backend` y `frontend`.

### 2.1 Backend (Python 3.11+, FastAPI)
- **Punto de Entrada**: `backend/src/api/main.py`.
- **Patrones**: 
  - Estado persistente y memoria del agente manejado mediante `thread_id` en `LangGraph` (con `MemorySaver`).
  - Nodos del agente desacoplados en `backend/src/agent/`.
- **Comando de Inicio**: `cd backend && uvicorn src.api.main:app --reload --port 8000`.

### 2.2 Frontend (Streamlit para Pruebas / Next.js para Prod)
- Interfaz base en `frontend/app.py` que consume el backend.

---

## 3. Lógica de Datos (`data/`)
El sistema se alimenta estrictamente de **2 archivos de datos oficiales** que debes usar para la base vectorial:
1. `ai_cases.csv`: Casos relacionados a Inteligencia Artificial.
2. `neo_legacy.csv`: Histórico general de casos legacy como recurso extra.

---

## 4. Directorios de Referencia para el Agente
Si necesitas mayor profundidad en algún requerimiento, consulta estrictamente estas carpetas organizadas:

- 📂 `MVP-V1-DOCS/`: Contiene los detalles históricos, bitácoras de errores (muy útil para debuggear) y el Baseline de la V1 (cómo funcionaba antes de refactorizar).
- 📂 `MVP-V2-DOCS/`: Especificaciones de arquitectura de V2, journeys de usuario, requisitos funcionales/técnicos y guías (SKILLS).

---

*Nota para la IA: Lee, comprende y asimila estas instrucciones antes de realizar modificaciones arquitectónicas o escribir código nuevo en este repositorio.*