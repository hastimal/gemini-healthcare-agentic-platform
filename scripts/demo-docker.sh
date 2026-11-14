#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-gemini}"
PORT="${DEMO_PORT:-8501}"

if [[ "$MODE" != "gemini" ]]; then
  echo "Notice: v1.3 local observability is Gemini-only. Running in gemini mode."
  MODE="gemini"
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

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "ERROR: GEMINI_API_KEY is not configured in .env."
  exit 1
fi
if [[ -z "${GEMINI_MODEL:-}" ]]; then
  echo "ERROR: GEMINI_MODEL is not configured in .env."
  exit 1
fi
export MODEL_PROVIDER="gemini"
export DEMO_PORT="$PORT"

echo "Building and starting local Dockerized healthcare observability stack..."
docker compose up --build -d

echo "Waiting for services to become healthy..."
SERVICES=("tempo" "prometheus" "otel-collector" "grafana" "healthcare-app")

for svc in "${SERVICES[@]}"; do
  echo "Checking health for $svc..."
  for _ in $(seq 1 60); do
    CONTAINER_ID="$(docker compose ps -q "$svc" 2>/dev/null || true)"
    if [[ -z "$CONTAINER_ID" ]]; then
      sleep 2
      continue
    fi
    STATUS="$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER_ID" 2>/dev/null || true)"
    if [[ "$STATUS" == "healthy" || "$STATUS" == "running" ]]; then
      # If container has healthcheck, wait until it is 'healthy'
      HAS_HEALTHCHECK="$(docker inspect --format='{{if .State.Health}}yes{{else}}no{{end}}' "$CONTAINER_ID" 2>/dev/null || true)"
      if [[ "$HAS_HEALTHCHECK" == "yes" && "$STATUS" != "healthy" ]]; then
        sleep 2
        continue
      fi
      break
    fi

    if [[ "$STATUS" == "unhealthy" || "$STATUS" == "exited" ]]; then
      echo "ERROR: $svc became $STATUS."
      docker compose logs --tail=50 "$svc" || true
      exit 1
    fi
    sleep 2
  done
done

echo
echo "============================================================"
echo " Gemini Healthcare Agentic Platform READY"
echo "============================================================"
echo " Healthcare UI: http://localhost:${PORT}"
echo " Grafana:       http://localhost:3000"
echo " Prometheus:    http://localhost:9090"
echo " Tempo:         http://localhost:3200"
echo
echo " Model: GEMINI"
echo " Gemini model: ${GEMINI_MODEL}"
echo
echo " Logs:"
echo " docker compose logs -f"
echo
echo " Stop:"
echo " ./scripts/demo-docker-stop.sh"
echo "============================================================"

if command -v open >/dev/null 2>&1; then
  open "http://localhost:$PORT" >/dev/null 2>&1 || true
fi
