#!/bin/bash

# ==========================================
# HOW TO RUN THE MVP-2 (V2 Refactored Architecture)
# ==========================================
#
# Terminal 1: START BACKEND
# ------------------------------------------
# 1. Activate env: source my_venv/bin/activate
# 2. cd backend
# 3. Start API: uvicorn src.api.main:app --reload --port 8000
#
# Terminal 2: START FRONTEND
# ------------------------------------------
# 1. Activate env: source my_venv/bin/activate
# 2. cd frontend
# 3. Start UI: streamlit run app.py
#
# The API will be on http://localhost:8000
# The UI will be on http://localhost:8501
