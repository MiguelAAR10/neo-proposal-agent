# NEO Proposal Agent (V2)

Aplicación para generar propuestas comerciales asistidas por IA con arquitectura Backend-First:

- `backend/`: FastAPI + LangGraph + integraciones (Qdrant/Gemini/Redis).
- `frontend-web/`: Next.js (UI principal V2).
- `frontend/`: Streamlit legado de V1 (solo referencia histórica).

## Requisitos

1. Python 3.11+
2. Node.js 20+
3. npm 10+

## Configuración de entorno

Desde la raíz del repo:

```bash
cp .env.example .env
```

Variables mínimas recomendadas en `.env` (backend):

```env
# Qdrant
QDRANT_URL=https://tu-cluster.qdrant.tech
QDRANT_API_KEY=tu_api_key
QDRANT_COLLECTION_CASES=neo_cases_v1
QDRANT_COLLECTION_PROFILES=neo_profiles_v1

# Redis (opcional en local)
REDIS_URL=redis://localhost:6379

# Gemini
GEMINI_API_KEY=tu_gemini_api_key
GEMINI_CHAT_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001

# App
APP_ENV=development
```

Para el frontend, usa `frontend-web/.env.local` si necesitas cambiar la URL del backend:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Instalación de dependencias

```bash
python -m venv my_venv
source my_venv/bin/activate
python -m pip install -r backend/requirements.txt
npm --prefix frontend-web install
```

## Arranque local V2

Terminal 1 (backend):

```bash
source my_venv/bin/activate
python -m uvicorn src.api.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Terminal 2 (frontend):

```bash
npm --prefix frontend-web run dev -- -H 127.0.0.1 -p 3000
```

URLs:

- API: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:3000`

## Verificación rápida

```bash
curl -sS http://127.0.0.1:8000/health
curl -I http://127.0.0.1:3000
```

Notas:

- En local, `/health` puede devolver `status: "degraded"` si Qdrant/Redis no están disponibles.
- El backend puede iniciar con `MemorySaver` cuando Redis no está configurado.

## Endpoints V2 principales

- `POST /agent/start`
- `POST /agent/{thread_id}/select`
- `POST /agent/{thread_id}/chat`
- `POST /agent/{thread_id}/refine`
- `GET /agent/{thread_id}/state`
- `GET /ops/*` (panel operativo)

## Prueba de flujo

```bash
source my_venv/bin/activate
python -u test_v2_flow.py
```

Depende de servicios externos (Qdrant/Gemini). Si no están accesibles, puede fallar por timeout.

## Documentación adicional

- `MVP-V2-DOCS/BITACORA_MVP_V2.md`
- `MVP-V2-DOCS/00-INDEX-DOCUMENTATION.md`
- `MVP-V2-DOCS/REQUIREMENTS/02-ARQUITECTURA-SISTEMA.md`
