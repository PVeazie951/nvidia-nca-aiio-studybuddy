#!/usr/bin/env bash
# Start the NVIDIA NCA-AIIO Study Buddy (backend + frontend).
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p data/uploads logs

if ! pg_isready -h 127.0.0.1 -q 2>/dev/null; then
  echo "Postgres not responding on 127.0.0.1:5432 — starting it (needs sudo)"
  sudo systemctl start postgresql
  sleep 2
fi

if [ ! -d .venv ]; then
  echo "Creating venv…"
  /usr/bin/python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r backend/requirements.txt
fi

if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend deps…"
  (cd frontend && npm install --no-fund --no-audit)
fi

echo "Starting backend on http://127.0.0.1:8077"
.venv/bin/python -m uvicorn app.main:app --app-dir backend \
  --host 127.0.0.1 --port 8077 > logs/backend.log 2>&1 &
echo $! > logs/backend.pid

sleep 3
echo "Starting frontend on http://127.0.0.1:5273"
(cd frontend && node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5273 --strictPort) \
  > logs/frontend.log 2>&1 &
echo $! > logs/frontend.pid

sleep 3
echo
echo "  Study Buddy:  http://127.0.0.1:5273"
echo "  API docs:     http://127.0.0.1:8077/docs"
echo
echo "Open Settings in the UI to point at your model endpoint."
echo "Logs: logs/backend.log, logs/frontend.log"
echo "Stop with: ./stop.sh"
