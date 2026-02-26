# Bitácora de Aprendizaje y Resolución de Problemas - NEO Proposal Agent (V1)

Este documento recopila las lecciones clave aprendidas durante el desarrollo de la Versión 1, sirviendo como guía fundamental para evitar errores estructurales en la Versión 2 y futuros proyectos.

## 1. La Arquitectura Backend First (FastAPI vs Streamlit)
**El Problema (Anti-patrón):** Inicialmente, existe la tentación de poner lógica de negocio (llamadas directas a Qdrant, invocación de LLMs, gestión de LangGraph) dentro de `app.py` (Streamlit) para iterar rápido. Esto causa bloqueos en la interfaz visual, pérdida de sesiones, y hace que los errores (como un Error 500) sean muy difíciles de rastrear.
**El Aprendizaje:** 
- Streamlit debe ser **estrictamente una capa de presentación (Dumb UI)**. Solo debe enviar requests HTTP y pintar JSONs.
- **FastAPI debe ser el núcleo desde el Día 1.** Todo el procesamiento pesado, las reglas de LangGraph y las conexiones a bases de datos deben residir en endpoints como `/agent/run` o `/search`.
- Esto permite probar la lógica de negocio de manera aislada (usando Swagger/cURL) sin depender de que la interfaz gráfica funcione.

## 2. Inyección de Dependencias y Variables de Entorno
**El Problema:** Importar clientes globales (como `QdrantClient` o `genai.Client`) directamente en el nivel superior de los scripts causa que las conexiones intenten establecerse antes de que el archivo `.env` se lea correctamente. También genera dependencias circulares si varios archivos se importan entre sí.
**El Aprendizaje:**
- **Lazy Initialization / Patrón Lifespan:** En FastAPI, las conexiones externas deben inicializarse dentro del bloque `lifespan` al arrancar el servidor.
- **Gestión centralizada:** Usar `src/config.py` (preferiblemente con `pydantic-settings`) como única fuente de la verdad para leer el `.env`. Ningún otro archivo debe usar `os.getenv()` directamente. Ningún nombre de modelo (ej. `gemini-embedding-001`) debe estar "quemado" (hardcoded) en la lógica.

## 3. Gestión de Versiones de Modelos y Librerías (`requirements.txt`)
**El Problema:** Las actualizaciones silenciosas rompen el código. Durante la V1, el modelo de embeddings `text-embedding-004` fue apagado por Google, causando fallos críticos 404. Además, versiones desajustadas del cliente de Qdrant generaban advertencias de incompatibilidad.
**El Aprendizaje:**
- Fijar las versiones exactas de las librerías en producción (`libreria==1.2.3` en lugar de `>=`).
- Construir mecanismos de "Fallback" (respaldo) en el código. Si un modelo falla, el sistema debe saber intentar con un modelo secundario o lanzar un log de error claro.

## 4. El Peligro de las Bases de Datos Vectoriales sin Índices
**El Problema:** La API de FastAPI devolvía un Error 500 de servidor. Al investigar, Qdrant rechazaba la solicitud de búsqueda porque estábamos intentando filtrar por "industria" y el campo no estaba indexado.
**El Aprendizaje:**
- Guardar vectores no es suficiente. Si se van a usar filtros condicionales (metadatos), **es obligatorio crear índices de payload (Payload Indexes)** en la base de datos antes de consultar. 
- Esto implica que el pipeline de datos (`load_data.py`) debe no solo subir datos, sino configurar la estructura de la base de datos (índices `KEYWORD`).

## 5. Resiliencia del Frontend (Componentes Nativos vs HTML Crudo)
**El Problema:** Al forzar diseño mediante cadenas de HTML crudo (con indentaciones incorrectas), Streamlit fallaba al parsearlo y lo renderizaba como código puro (el error de los tags `<dic>` en pantalla).
**El Aprendizaje:**
- Reducir al mínimo el uso de `unsafe_allow_html=True`.
- Es mucho más estable y fluido utilizar los componentes nativos de layout de Streamlit (`st.columns`, `st.chat_message`, `st.container`). Asegura que los tipos de datos que devuelve la API (diccionarios vs strings) sean procesados y parseados correctamente antes de enviarse a la pantalla.