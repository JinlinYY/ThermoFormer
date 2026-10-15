#!/usr/bin/env bash
set -euo pipefail
port="${PORT:-8000}"
web_root="$(cd "$(dirname "$0")/.." && pwd)"
repo_root="$(cd "$web_root/../.." && pwd)"
backend_root="$web_root/backend"
export PYTHONPATH="$backend_root"
export KNOWLEDGE_ROOT="$backend_root/knowledge"
export THERMOFORMER_SRC="$repo_root/src"
export THERMOFORMER_FEATURE_CACHE="$backend_root/.thermoformer-cache"
export THERMO_EXPERIENCE_DB="$backend_root/data/agent_experience.sqlite3"
cd "$backend_root"
exec python -m uvicorn main:app --reload --host 127.0.0.1 --port "$port"
