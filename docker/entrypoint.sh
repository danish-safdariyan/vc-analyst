#!/bin/sh
set -e
mkdir -p /work/backend/.analysis_jobs
export PATH="/venv/bin:${PATH}"
export BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"

cd /work/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

cd /work/web
exec node server.js
