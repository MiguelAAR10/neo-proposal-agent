#!/usr/bin/env bash
# NEO V4 — Run seed script to populate Qdrant Cloud + SQLite
# Usage: cd backend && bash run_seed.sh

set -euo pipefail

echo "=== NEO V4 Seed Script ==="
echo "Step 0: Installing/verifying dependencies..."
pip install -q -r requirements.txt 2>/dev/null || pip3 install -q -r requirements.txt

echo "Step 1: Running seed_v4_data.py..."
python -m scripts.seed_v4_data 2>&1 || python3 -m scripts.seed_v4_data 2>&1

echo ""
echo "=== Seed complete. Start the backend with: ==="
echo "  cd backend && uvicorn src.api.main:app --reload --port 8000"
