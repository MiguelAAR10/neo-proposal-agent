# NEO Proposal Agent (V2 en curso)

Plataforma para generar propuestas comerciales asistidas por IA usando una arquitectura **Backend-First** con **FastAPI + LangGraph + Qdrant** y UI principal en **Next.js**.

Este repositorio mantiene artefactos de V1 (Streamlit) por continuidad histórica, pero el flujo objetivo de V2 corre en `backend/` + `frontend-web/`.

## Estado actual del desarrollo

- Backend V2 operativo con flujo HITL (Human in the Loop):
  - `POST /agent/start`
  - `POST /agent/{thread_id}/select`
  - `GET /agent/{thread_id}/state`
- Frontend Next.js integrado para:
  - intake inicial
  - curación/selección de casos
  - generación de propuesta final
- Pendiente principal: conectar `ChatPanel` del frontend web a endpoint de chat real de backend (hoy está mockeado).
- Streamlit (`frontend/app.py`) se considera **legacy de V1** y no representa el contrato API actual de V2.

## Estructura del proyecto

```text
backend/         FastAPI + LangGraph + integraciones Qdrant/Gemini
frontend-web/    Next.js (UI V2 principal)
frontend/        Streamlit legacy (V1, referencia)
MVP-V2-DOCS/     Requisitos, arquitectura y bitácora V2
```

## Requisitos

1. Python 3.11+
2. Node.js 20+
3. Variables en `.env` (raíz del repo):

```env
QDRANT_URL="..."
QDRANT_API_KEY="..."
GEMINI_API_KEY="..."
REDIS_URL="redis://localhost:6379"
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

## Arranque V2 (recomendado)

### Terminal 1: Backend

```bash
source my_venv/bin/activate
cd backend
uvicorn src.api.main:app --reload --port 8000
```

### Terminal 2: Frontend Web (Next.js)

```bash
cd frontend-web
npm install
npm run dev
```

- API: `http://localhost:8000`
- UI Web: `http://localhost:3000`

## Flujo funcional V2

1. Completar formulario inicial (empresa, rubro, área, problema, switch).
2. Backend ejecuta `intake_node` + `retrieve_node` y devuelve casos sugeridos.
3. Usuario selecciona casos relevantes.
4. Backend continúa `draft_node` y genera propuesta final.

## Pruebas rápidas

```bash
python -u test_v2_flow.py
```

Nota: esta prueba depende de servicios externos (Qdrant/Gemini). Si no están accesibles, puede quedar en timeout.

## Documentación clave

- Estado y decisiones V2: `MVP-V2-DOCS/BITACORA_MVP_V2.md`
- Índice general: `MVP-V2-DOCS/00-INDEX-DOCUMENTATION.md`
- Arquitectura objetivo: `MVP-V2-DOCS/REQUIREMENTS/02-ARQUITECTURA-SISTEMA.md`

## Convención de evolución

- Mantener backend como fuente de verdad del negocio.
- Frontend como capa de presentación.
- Registrar decisiones técnicas en la bitácora V2 (no solo cambios de código).
