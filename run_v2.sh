#!/bin/bash

# ==========================================
# HOW TO RUN MVP-2 (V2 Backend-First)
# ==========================================
#
# Opción recomendada (actual): FastAPI + Next.js
# -----------------------------------------------
# Terminal 1 (Backend)
# 1. source my_venv/bin/activate
# 2. cd backend
# 3. uvicorn src.api.main:app --reload --port 8000
#
# Terminal 2 (Frontend Web)
# 1. cd frontend-web
# 2. npm install
# 3. npm run dev
#
# API: http://localhost:8000
# UI:  http://localhost:3000
#
# Nota de compatibilidad:
# - frontend/app.py (Streamlit) es legado de V1 y no está alineado al contrato API V2
#   (/agent/start, /agent/{thread_id}/select, /agent/{thread_id}/state).
