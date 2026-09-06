#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-gemini}"
PORT="${DEMO_PORT:-8501}"

if [[ "$MODE" != "gemini" && "$MODE" != "gemma" ]]; then
  echo "Usage: ./scripts/demo-docker.sh [gemini|gemma]"
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found."
  echo "Create it from .env.example and configure Gemini."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

if [[ "$MODE" == "gemini" ]]; then
  if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "ERROR: GEMINI_API_KEY is not configured in .env."
    exit 1
  fi
  if [[ -z "${GEMINI_MODEL:-}" ]]; then
    echo "ERROR: GEMINI_MODEL is not configured in .env."
    exit 1
  fi
  export MODEL_PROVIDER="gemini"
else
  export MODEL_PROVIDER="gemma"
  export GEMMA_MODEL="${GEMMA_MODEL:-gemma4:12b}"
  export OLLAMA_BASE_URL="http://host.docker.internal:11434"

  if ! curl -fsS "http://localhost:11434/api/tags" >/dev/null 2>&1; then
    echo "ERROR: native Ollama is not reachable at http://localhost:11434."
    echo "Start Ollama on macOS, then retry."
    exit 1
  fi

  if ! curl -fsS "http://localhost:11434/api/tags" | grep -q "\"name\":\"${GEMMA_MODEL}\""; then
    echo "ERROR: ${GEMMA_MODEL} is not installed in native Ollama."
    echo "Install it with: ollama pull ${GEMMA_MODEL}"
    exit 1
  fi
fi

export DEMO_PORT="$PORT"

echo "Building and starting Dockerized healthcare demo..."
docker compose up --build -d healthcare-app

echo "Waiting for Streamlit health check..."
for _ in $(seq 1 60); do
  CONTAINER_ID="$(docker compose ps -q healthcare-app)"
  STATUS="$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_ID" 2>/dev/null || true)"
  if [[ "$STATUS" == "healthy" ]]; then
    echo
    echo "============================================================"
    echo " Docker Healthcare Agentic Platform READY"
    echo "============================================================"
    if [[ "$MODE" == "gemini" ]]; then
      echo " Model: GEMINI"
      echo " Gemini model: ${GEMINI_MODEL}"
    else
      echo " Model: GEMMA"
      echo " Gemma model: ${GEMMA_MODEL}"
      echo " Ollama: native macOS via host.docker.internal:11434"
    fi
    echo
    printf "[1;32m"
    echo " ┌──────────────────────────────────────────────┐"
    echo " │  ✓ DOCKER DEMO READY                        │"
    printf " │  OPEN: http://localhost:%-20s │
" "$PORT"
    echo " └──────────────────────────────────────────────┘"
    printf "[0m"
    echo
    echo " Logs: docker compose logs -f healthcare-app"
    echo " Stop: ./scripts/demo-docker-stop.sh"
    echo "============================================================"

    if command -v open >/dev/null 2>&1; then
      open "http://localhost:$PORT" >/dev/null 2>&1 || true
    fi
    exit 0
  fi

  if [[ "$STATUS" == "unhealthy" ]]; then
    echo "ERROR: container became unhealthy."
    docker compose logs --tail=120 healthcare-app || true
    exit 1
  fi

  sleep 2
done

echo "ERROR: Dockerized GUI did not become healthy in time."
docker compose ps
docker compose logs --tail=120 healthcare-app || true
exit 1
