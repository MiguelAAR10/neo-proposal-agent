# NEO Proposal Agent

MVP para generar propuestas comerciales con LangGraph + Streamlit usando casos almacenados en Qdrant.

## 1) Activar entorno

```bash
source my_venv/bin/activate
```

## 2) Verificar variables de entorno (`.env`)

Debes tener al menos:

- `QDRANT_URL`
- `QDRANT_API_KEY` (si tu Qdrant lo requiere)
- `GEMINI_API_KEY`

Opcional para forzar modelo de embeddings:

- `GEMINI_EMBEDDING_MODEL` (por ejemplo `models/embedding-001`)

## 3) Procesar CSV y cargar colección en Qdrant

```bash
python -m src.tools.load_csv_to_qdrant
```

Esto procesa todos los `*.csv` dentro de `data/` y los sube a la colección `neo_cases_v1`.

## 4) Levantar la aplicación

```bash
streamlit run app.py
```

## 5) Flujo en UI

1. Completa Empresa, Rubro y Problema.
2. Clic en **Buscar Casos**.
3. Selecciona casos en la pausa HITL.
4. Clic en **Generar Propuesta**.

## Problemas comunes

### Error `404 ... text-embedding-004 not found`

El proyecto ahora prueba varios modelos de embedding automáticamente.
Si persiste, fija explícitamente en `.env`:

```env
GEMINI_EMBEDDING_MODEL=models/embedding-001
```

### Se quedó con estado viejo / formulario bloqueado

Usa **Nueva Sesion** en la barra lateral, o vuelve a enviar el formulario (cada búsqueda crea un thread nuevo).
