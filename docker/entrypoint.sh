#!/bin/sh
set -e
export VC_ANALYSIS_JOBS_DIR="${VC_ANALYSIS_JOBS_DIR:-/tmp/vc-analysis-jobs}"
mkdir -p "$VC_ANALYSIS_JOBS_DIR"
export PATH="/venv/bin:${PATH}"
export BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
export INTERNAL_FASTAPI_URL="${INTERNAL_FASTAPI_URL:-http://127.0.0.1:8000}"

cd /work/backend
# Single worker: in-memory job cache must match the process handling polls.
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 &

cd /work/web
exec node server.js
