# NEO Proposal Agent (V1 Finalizada)

MVP para generar y descubrir propuestas comerciales usando **LangGraph**, **FastAPI**, **Streamlit** y **Qdrant**.

El sistema ha sido reestructurado hacia una arquitectura "Backend-First". Esto significa que la interfaz (Streamlit) sirve únicamente para renderizar la pantalla, mientras que todo el procesamiento pesado (LLMs, base vectorial y estados del agente) se expone a través de una robusta API en FastAPI.

## 1) Instalación y Entorno

1. **Activar tu entorno virtual**
   ```bash
   source my_venv/bin/activate
   ```
2. **Instalar dependencias**
   Asegúrate de instalar los paquetes fijados para evitar incompatibilidades.
   ```bash
   pip install -r requirements.txt
   ```

## 2) Variables de Entorno (`.env`)

Debes crear un archivo `.env` en la raíz (puedes basarte en `.env.example`).
Tus variables mínimas indispensables son:

```env
QDRANT_URL="URL_A_TU_CLUSTER"
QDRANT_API_KEY="TU_CLAVE_DE_QDRANT"
GEMINI_API_KEY="TU_CLAVE_DE_GOOGLE_AI_STUDIO"
```

*Nota: Asegúrate de configurar modelos compatibles vigentes, por ejemplo, `gemini-embedding-001` (ya que versiones como `text-embedding-004` han sido apagadas y generarán fallos).*

## 3) Procesar y Cargar Datos a Qdrant

Para poblar tu base de datos vectorial con los casos y crear los índices de filtro necesarios:

```bash
python load_data.py
```
*(O el script de ingesta de datos en lote configurado, que crea la colección, extrae vectores y establece las llaves `industria` y `area_funcional` en Qdrant).*

## 4) Levantar la Aplicación (Split-Screen UI)

Como la V1 consolida una arquitectura backend/frontend separada, **debes correr ambos servicios** simultáneamente en dos terminales.

**Terminal 1 (Backend - FastAPI)**
```bash
uvicorn api:app --reload --port 8000
```
*Asegúrate de que la API levante correctamente y diga "✅ Clients ready".*

**Terminal 2 (Frontend - Streamlit)**
```bash
streamlit run app.py
```

## 5) Flujo Funcional (UI V1)

1. En la aplicación web (ej. `http://localhost:8501`), completa la descripción del problema de tu cliente en el área principal.
2. (Opcional) Usa los filtros de Industria o Área Funcional en la barra lateral izquierda.
3. Haz clic en **⚡ Buscar Casos Relevantes**.
4. Disfruta de la nueva interfaz dividida:
   - **Izquierda (Casos):** Tarjetas visuales de los casos encontrados, ordenados por score.
   - **Derecha (Chat Inteligente):** Usa el chat nativo de Streamlit ("NEO Assistant") para preguntarle directamente sobre cómo aplicar esos casos a tu cliente actual o para pedirle un *pitch*.

## Problemas Comunes y Troubleshooting

- **Error 500 al buscar:** Ocurre si la API de FastAPI falla. Revisa los logs de la consola donde corre `uvicorn`. La causa principal es que Qdrant no tenga los índices creados (`Payload Index`) para los filtros. Asegúrate de haber corrido correctamente los scripts de carga.
- **Error 404 (Embedding Model Not Found):** Google ha retirado modelos antiguos. Asegúrate de que el backend no tenga inicializado (`hardcoded`) `text-embedding-004` ni en `api.py` ni en `src/config.py`. Usa `gemini-embedding-001`.
- **"❌ No se pudo conectar con la API" en Streamlit:** Significa que `app.py` no puede encontrar el backend. Verifica que `uvicorn` siga corriendo en el puerto 8000.

## Documentación Técnica

Para entender a fondo la lógica de conexión entre FastAPI, el orquestador LangGraph, y Qdrant, así como los planes para la Versión 2, lee `mvp-v1-memoria-fundacional/PROJECT_DETAILS.md`. Para revisar las lecciones aprendidas durante la construcción de la V1 y evitar anti-patrones, lee `mvp-v1-memoria-fundacional/BITACORA_APRENDIZAJES.md`. Como diagnóstico de organización histórica, consulta `mvp-v1-memoria-fundacional/RADIOGRAFIA_PROYECTO.md`.
