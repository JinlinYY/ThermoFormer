#!/usr/bin/env bash
set -euo pipefail
port="${PORT:-3000}"
api_url="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
web_root="$(cd "$(dirname "$0")/.." && pwd)"
export NEXT_PUBLIC_API_URL="$api_url"
cd "$web_root/frontend"
exec pnpm dev --hostname 127.0.0.1 --port "$port"
