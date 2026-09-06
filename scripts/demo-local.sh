#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-gemini}"
PORT="${DEMO_PORT:-8501}"
DEMO_DIR="$ROOT_DIR/.demo"
PID_FILE="$DEMO_DIR/streamlit.pid"
LOG_FILE="$DEMO_DIR/streamlit.log"
OLLAMA_PID_FILE="$DEMO_DIR/ollama.pid"
OLLAMA_LOG_FILE="$DEMO_DIR/ollama.log"

mkdir -p "$DEMO_DIR"

if [[ "$MODE" != "gemini" && "$MODE" != "gemma" ]]; then
  echo "Usage: ./scripts/demo-local.sh [gemini|gemma]"
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found."
  echo "Create it from .env.example and configure the selected model."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

export MODEL_PROVIDER="$MODE"

if [[ -f "$PID_FILE" ]]; then
  EXISTING_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$EXISTING_PID" ]] && kill -0 "$EXISTING_PID" 2>/dev/null; then
    echo "Demo is already running with PID $EXISTING_PID."
    echo "Open: http://localhost:$PORT"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

if [[ "$MODE" == "gemini" ]]; then
  if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "ERROR: GEMINI_API_KEY is not configured in .env."
    exit 1
  fi

  if [[ -z "${GEMINI_MODEL:-}" ]]; then
    echo "ERROR: GEMINI_MODEL is not configured in .env."
    exit 1
  fi
fi

if [[ "$MODE" == "gemma" ]]; then
  if ! command -v ollama >/dev/null 2>&1; then
    echo "ERROR: Ollama is not installed."
    echo "Install Ollama before running the local Gemma demo."
    exit 1
  fi

  if [[ -z "${GEMMA_MODEL:-}" ]]; then
    echo "ERROR: GEMMA_MODEL is not configured in .env."
    exit 1
  fi

  OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
  export OLLAMA_BASE_URL

  if ! curl -fsS "$OLLAMA_BASE_URL/api/tags" >/dev/null 2>&1; then
    echo "Starting Ollama..."
    nohup ollama serve >"$OLLAMA_LOG_FILE" 2>&1 &
    echo $! > "$OLLAMA_PID_FILE"

    for _ in {1..30}; do
      if curl -fsS "$OLLAMA_BASE_URL/api/tags" >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
  fi

  if ! curl -fsS "$OLLAMA_BASE_URL/api/tags" >/dev/null 2>&1; then
    echo "ERROR: Ollama did not become ready."
    echo "See: $OLLAMA_LOG_FILE"
    exit 1
  fi

  if ! ollama list | awk 'NR>1 {print $1}' | grep -Fxq "$GEMMA_MODEL"; then
    echo "Gemma model '$GEMMA_MODEL' is not installed locally."
    echo "Pulling it now. This can take a while on the first run..."
    ollama pull "$GEMMA_MODEL"
  fi
fi

if ! python -c "import streamlit" >/dev/null 2>&1; then
  echo "ERROR: Streamlit is not installed."
  echo "Run: ./scripts/setup-gui-demo.sh"
  exit 1
fi

echo "Starting healthcare agentic GUI..."
nohup python -m streamlit run ui/streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port "$PORT" \
  --server.headless true \
  >"$LOG_FILE" 2>&1 &

STREAMLIT_PID=$!
echo "$STREAMLIT_PID" > "$PID_FILE"

for _ in {1..30}; do
  if curl -fsS "http://localhost:$PORT/_stcore/health" >/dev/null 2>&1; then
    echo
    echo "============================================================"
    echo " Healthcare Agentic Platform Demo READY"
    echo "============================================================"
    echo " Model: $(printf "%s" "$MODE" | tr "[:lower:]" "[:upper:]")"
    if [[ "$MODE" == "gemma" ]]; then
      echo " Gemma model: ${GEMMA_MODEL}"
      echo " Ollama: ${OLLAMA_BASE_URL}"
    else
      echo " Gemini model: ${GEMINI_MODEL}"
    fi
    echo
    printf "\033[1;32m"
    echo " ┌──────────────────────────────────────────────┐"
    echo " │  ✓ DEMO READY                               │"
    printf " │  OPEN: http://localhost:%-20s │\n" "$PORT"
    echo " └──────────────────────────────────────────────┘"
    printf "\033[0m"
    echo
    echo " Logs: $LOG_FILE"
    echo
    echo " Stop: ./scripts/demo-stop.sh"
    echo "============================================================"

    if command -v open >/dev/null 2>&1; then
      open "http://localhost:$PORT" >/dev/null 2>&1 || true
    fi
    exit 0
  fi

  if ! kill -0 "$STREAMLIT_PID" 2>/dev/null; then
    echo "ERROR: Streamlit exited before becoming ready."
    echo "See log:"
    tail -80 "$LOG_FILE" || true
    rm -f "$PID_FILE"
    exit 1
  fi

  sleep 1
done

echo "ERROR: GUI did not become ready within 30 seconds."
echo "See: $LOG_FILE"
exit 1
