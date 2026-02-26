# NEO Proposal Agent - Proyecto Detalle

Este documento detalla la arquitectura técnica, la lógica de negocio y los componentes del proyecto **NEO Proposal Agent**. Refleja el estado consolidado de la **Versión 1 (V1)**, la cual ya implementa una arquitectura separada (Frontend en Streamlit, Backend en FastAPI) e integración completa con LangGraph y Qdrant.

## 1. Lógica de Negocio
El objetivo del agente es actuar como un copiloto experto (NEO Assistant) para los consultores, automatizando el descubrimiento de casos de éxito y la ideación de propuestas de valor.
- **Entrada:** Descripción en lenguaje natural del problema o necesidad del cliente, con filtros opcionales por industria y área funcional.
- **Proceso:** El backend, orquestado con LangGraph, procesa el texto, genera embeddings (Gemini) y realiza una búsqueda semántica y filtrada en una base de datos vectorial (Qdrant).
- **Asistencia Activa (Chat RAG):** El consultor visualiza los casos más relevantes y utiliza un chat inteligente (alimentado por Gemini Flash) que tiene contexto completo de los casos encontrados para resolver dudas técnicas, extraer ideas o redactar borradores de propuestas ("pitches").
- **Salida:** Casos de éxito validados y material de propuesta de valor generado iterativamente en el chat.

## 2. Arquitectura Técnica (V1 Consolidada)
El sistema está construido siguiendo el paradigma "Backend-First" para asegurar escalabilidad y estabilidad.

### Componentes Core:
- **Frontend (Dumb UI):** Streamlit (`app.py`). Interfaz de usuario pura. No procesa lógica pesada, solo envía peticiones HTTP y renderiza la pantalla dividida (Tarjetas de Casos + Chat Nativo RAG).
- **Backend (API Central):** FastAPI (`src/api/main.py`). Expone los endpoints (ej. `/agent/run`) que consumen la lógica de LangGraph y Qdrant. Implementa inicialización segura ("Lazy Initialization") usando el patrón `lifespan` para las conexiones.
- **Orquestador Lógico:** LangGraph (`src/agent/graph.py` y `src/agent/nodes.py`). Define el flujo de estados del agente, desde la ingesta de la petición hasta la recuperación de casos.
- **Base de Datos Vectorial:** Qdrant en la nube (Qdrant Cloud). Almacena los casos procesados. Utiliza **Payload Indexes** (índices `KEYWORD`) para permitir filtros rápidos por `industria` y `area_funcional`.
- **LLM y Embeddings:** Google Gemini. Se usa `gemini-3-flash-preview` (o la versión vigente) para el razonamiento y la generación en el chat, y `gemini-embedding-001` para vectorizar los textos.

## 3. Variables de Entorno y Configuración
El archivo central de configuración es `src/config.py`, el cual carga de forma segura las variables desde un archivo `.env` en la raíz.

| Variable | Descripción |
| :--- | :--- |
| `QDRANT_URL` | Endpoint de la base de datos Qdrant en la nube. |
| `QDRANT_API_KEY` | Clave de acceso a Qdrant. |
| `GEMINI_API_KEY` | Clave de API de Google AI Studio para los modelos LLM y de embeddings. |

*Nota: Cualquier cambio de modelo de embeddings o versión del LLM debe hacerse de forma controlada y con validación, ya que versiones obsoletas (como `text-embedding-004`) generarán fallos críticos de tipo 404.*

## 4. Estructura de Módulos Clave

### `src/agent/`
- **`state.py`**: Define la estructura de datos que viaja por el grafo (estado del agente).
- **`nodes.py`**: Contiene los nodos lógicos del grafo (validación, recuperación en Qdrant, invocación del LLM).
- **`graph.py`**: Compila y expone el flujo del agente, conectando los nodos de principio a fin.

### `src/tools/`
- **`qdrant_tool.py`**: Contiene la clase para la conexión a la base vectorial, encargada de la búsqueda semántica, la normalización de la carga útil (payload) y la integración con el modelo de embeddings actual.

### Raíz del Proyecto
- **`app.py`**: Interfaz de Streamlit (V1 finalizada con diseño de columnas divididas).
- **`api.py` / `src/api/main.py`**: Punto de entrada de FastAPI.
- **`load_data.py` / `load_data_new.py`**: Scripts de ingesta de datos en lote desde archivos CSV hacia Qdrant, encargados de crear la colección, generar vectores y establecer los índices necesarios.

## 5. Dependencias Principales (`requirements.txt`)
- `fastapi` & `uvicorn`: Para el servidor backend de alto rendimiento.
- `streamlit`: Para el frontend interactivo.
- `google-genai` / `langchain-google-genai`: Para el acceso a los modelos de razonamiento y embeddings de Google.
- `langgraph`: Para la orquestación del flujo del agente.
- `qdrant-client`: Conector oficial de la base de datos vectorial.
- `pydantic-settings`: Validación y gestión robusta de variables de entorno.

## 6. Próximos Pasos (V2) - Rama `feature/v2-fastapi-migration`
Con la V1 estabilizada y el frontend desacoplado (solo haciendo peticiones), la Versión 2 se enfocará netamente en capacidades profundas del backend:
1. **Memoria y Sesiones Persistentes:** Implementar `thread_id` en LangGraph gestionado a través de los endpoints de FastAPI para que el historial de chat se guarde de forma nativa en el backend y sobreviva a recargas de la página.
2. **Ingesta Automática Continua:** Crear un mecanismo (endpoint o cron-job) para actualizar o agregar nuevos casos a Qdrant de forma dinámica, en lugar de depender exclusivamente de scripts de carga en lote (`load_data.py`).
3. **Múltiples Agentes Especializados:** Extender el grafo para que el agente pueda tomar rutas distintas (ej. "Ruta de investigación de caso" vs "Ruta de redacción comercial").