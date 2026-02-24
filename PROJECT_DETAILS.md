# NEO Proposal Agent - Proyecto Detalle

Este documento detalla la arquitectura técnica, lógica de negocio y componentes del proyecto **NEO Proposal Agent**. Está diseñado para facilitar el escalamiento y la transición a una arquitectura basada en FastAPI (Versión 2).

## 1. Lógica de Negocio
El objetivo del agente es automatizar la creación de propuestas comerciales personalizadas.
- **Entrada:** Nombre de la empresa, rubro y el problema/necesidad detectada.
- **Proceso:** El agente busca en una base de datos vectorial (Qdrant) casos de éxito previos (proyectos "legacy") que se asemejen al problema actual.
- **HITL (Human-In-The-Loop):** El consultor revisa los casos encontrados y selecciona los más relevantes.
- **Salida:** Generación de una propuesta de valor estructurada usando un LLM (Gemini).

## 2. Arquitectura Técnica
El sistema está construido sobre un flujo agentico utilizando **LangGraph**.

### Componentes Core:
- **Orquestador:** `src/agent/graph.py` define el flujo de estados.
- **Base de Datos Vectorial:** Qdrant para almacenamiento y búsqueda semántica.
- **LLM:** Google Gemini (1.5 Flash para generación, Text Embedding 004 para vectores).
- **Frontend:** Streamlit (`app.py`) para validación rápida (V1).
- **Backend (Draft):** FastAPI (`src/api/main.py`) preparado para la V2.

## 3. Variables de Entorno y Configuración
Ubicadas en `src/config.py`, cargadas desde un archivo `.env`.

| Variable | Descripción |
| :--- | :--- |
| `QDRANT_URL` | Endpoint de la base de datos Qdrant. |
| `QDRANT_API_KEY` | Clave de acceso a Qdrant. |
| `GEMINI_API_KEY` | Clave de API de Google AI Studio. |
| `GEMINI_EMBEDDING_MODEL` | Modelo para generar embeddings (default: `models/text-embedding-004`). |

## 4. Estructura de Módulos y Funciones Clave

### `src/agent/`
- **`state.py`**: Define `ProposalState`, el diccionario que viaja por el grafo.
- **`nodes.py`**:
    - `intake_node`: Valida y limpia los datos de entrada.
    - `retrieve_node`: Llama a Qdrant para buscar casos similares.
    - `draft_node`: Invoca al LLM para redactar la propuesta final basada en los casos seleccionados.
- **`graph.py`**: Compila el grafo con un `interrupt_before=["draft_node"]` para permitir la selección manual de casos.

### `src/tools/`
- **`qdrant_tool.py`**: Clase `QdrantConnection`.
    - `search_cases(problem_text)`: Realiza la búsqueda semántica.
    - `upsert_cases(rows)`: Indexa nuevos casos en la colección `neo_cases_v1`.
    - `load_csv_files(paths)`: Carga masiva desde archivos CSV.

### `src/api/`
- **`main.py`**: Define los endpoints de FastAPI. *Nota: Requiere actualización para integrarse correctamente con el grafo compilado.*

## 5. Dependencias Principales (`requirements.txt`)
- `langgraph`: Orquestación de estados.
- `langchain-google-genai`: Integración con Gemini.
- `langchain-qdrant`: Conector vectorial.
- `fastapi` & `uvicorn`: Servidor backend.
- `streamlit`: Interfaz de usuario.

## 6. Próximos Pasos (V2)
1. **Refactorizar FastAPI:** Implementar endpoints que manejen el `thread_id` de LangGraph para sesiones persistentes.
2. **Migración de UI:** Mover la lógica de Streamlit a un frontend desacoplado que consuma la API.
3. **Ingesta Automática:** Crear un cron-job o endpoint para actualizar la base de casos desde nuevos CSVs.
