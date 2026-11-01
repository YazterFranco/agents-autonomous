#!/bin/sh
set -eu

MODE="${1:-api}"
MODEL="${OLLAMA_MODEL:-qwen2.5:7b}"
OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"

wait_for_ollama() {
  echo "Waiting for Ollama at ${OLLAMA_URL}..."
  i=0
  while [ "$i" -lt 60 ]; do
    if curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
      echo "Ollama is ready."
      return 0
    fi
    i=$((i + 1))
    sleep 2
  done
  echo "Ollama did not become ready in time." >&2
  return 1
}

ensure_model() {
  echo "Ensuring model ${MODEL} is available..."
  if curl -sf "${OLLAMA_URL}/api/tags" | grep -q "${MODEL%%:*}"; then
    echo "Model appears present."
    return 0
  fi
  curl -sf "${OLLAMA_URL}/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${MODEL}\"}" >/dev/null || true
}

mkdir -p "${AGENT_WORKSPACE:-/app/workspace}"
wait_for_ollama
ensure_model

case "$MODE" in
  api)
    exec uvicorn app.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}"
    ;;
  cli)
    shift
    exec python -m app "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
