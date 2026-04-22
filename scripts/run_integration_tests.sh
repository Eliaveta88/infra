#!/usr/bin/env bash
# Поднимает docker compose и прогоняет pytest tests_api против Traefik (по умолчанию http://localhost).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
API_BASE_URL="${API_BASE_URL:-http://localhost}"
MAX_WAIT_SEC="${MAX_WAIT_SEC:-120}"

echo "Compose: $COMPOSE_FILE"
docker compose -f "$COMPOSE_FILE" up -d --build

echo "Waiting for stack (max ${MAX_WAIT_SEC}s)..."
deadline=$((SECONDS + MAX_WAIT_SEC))
while (( SECONDS < deadline )); do
  if curl -sf "${API_BASE_URL}/catalog/api/v1/health" >/dev/null \
    && curl -sf "${API_BASE_URL}/identity/api/v1/health" >/dev/null; then
    echo "Stack is up."
    break
  fi
  sleep 3
done

if ! curl -sf "${API_BASE_URL}/catalog/api/v1/health" >/dev/null; then
  echo "Timeout: catalog health did not become ready." >&2
  exit 1
fi

python -m pip install -q -r tests_api/requirements.txt
export API_BASE_URL
exec python -m pytest tests_api -v "$@"
