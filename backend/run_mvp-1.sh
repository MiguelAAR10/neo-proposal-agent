#!/bin/bash

# ==========================================
# HOW TO RUN THE MVP-1 (Step-by-Step Guide)
# ==========================================
#
# To launch the application correctly, you need to run the Backend (API) 
# and the Frontend (UI) in two separate terminals.
#
# ------------------------------------------
# TERMINAL 1: Start the Backend (API)
# ------------------------------------------
# 1. Open your first terminal in the project root folder.
# 2. Activate the virtual environment:
#    source my_venv/bin/activate
# 3. Start the FastAPI backend server:
#    uvicorn api:app --reload --port 8000
#
# ------------------------------------------
# TERMINAL 2: Start the Frontend (UI)
# ------------------------------------------
# 1. Open a second terminal in the project root folder.
# 2. Activate the virtual environment again for this new session:
#    source my_venv/bin/activate
# 3. Start the Streamlit web application:
#    streamlit run app.py
#
# Once both are running, your browser should automatically open the Streamlit UI,
# or you can access it at http://localhost:8501. The API will be available at http://localhost:8000.
