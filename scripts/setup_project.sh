#!/usr/bin/env bash
# ---------------------------------------------------------------
# NEO Proposal Agent — Project Setup Script (MVP 2.1)
# Creates .venv, installs deps, and runs initial data ingestion.
# ---------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$PROJECT_ROOT/.venv"

echo "=== NEO Proposal Agent Setup ==="
echo "Project root: $PROJECT_ROOT"

# 1. Create virtualenv
if [ ! -d "$VENV_DIR" ]; then
  echo "[1/4] Creating virtualenv at $VENV_DIR ..."
  python3 -m venv "$VENV_DIR"
else
  echo "[1/4] Virtualenv already exists at $VENV_DIR"
fi

# 2. Activate and install dependencies
echo "[2/4] Installing backend dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -r "$BACKEND_DIR/requirements.txt" -q

# 3. Validate .env
if [ ! -f "$PROJECT_ROOT/.env" ]; then
  if [ -f "$PROJECT_ROOT/.env.example" ]; then
    echo "[3/4] Copying .env.example to .env — edit with your API keys."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  else
    echo "[3/4] WARNING: No .env or .env.example found. Create .env manually."
  fi
else
  echo "[3/4] .env already exists."
fi

# 4. Run Qdrant ingestion (requires Qdrant running and QDRANT_URL in .env)
echo "[4/4] Running initial data ingestion..."
if [ -f "$PROJECT_ROOT/data/ai_cases.csv" ] || [ -f "$PROJECT_ROOT/data/neo_legacy.csv" ]; then
  cd "$BACKEND_DIR"
  python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.tools.qdrant_tool import db_connection
    csvs = []
    import os
    data_dir = os.path.join('..', 'data')
    for name in ['ai_cases.csv', 'neo_legacy.csv']:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            csvs.append(path)
    if csvs:
        result = db_connection.load_csv_files(csvs, 'neo_cases_v1')
        print(f'Ingestion complete: {result}')
    else:
        print('No CSV files found in data/ — skipping ingestion.')
except Exception as e:
    print(f'Ingestion skipped (Qdrant may not be running): {e}')
"
else
  echo "No CSV data files found in data/ — skipping ingestion."
fi

echo ""
echo "=== Setup complete ==="
echo "To start the backend:  source .venv/bin/activate && cd backend && uvicorn src.api.main:app --reload"
echo "To start the frontend: cd frontend-web && npm install && npm run dev"
