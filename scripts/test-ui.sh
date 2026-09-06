#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-gemini}"
MODE="$(printf "%s" "$MODE" | tr "[:upper:]" "[:lower:]")"

if [ "$MODE" != "gemini" ] && [ "$MODE" != "gemma" ]; then
    echo "Usage: ./scripts/test-ui.sh <gemini|gemma>"
    exit 2
fi

if [ ! -d ".venv" ]; then
    echo "ERROR: .venv not found."
    echo "Activate/create the project environment before running UI acceptance."
    exit 1
fi

# Load local environment without printing secrets.
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    . ".env"
    set +a
fi

export MODEL_PROVIDER="$MODE"
export RUN_LIVE_UI_E2E=1

if [ "$MODE" = "gemini" ]; then
    if [ -z "${GEMINI_API_KEY:-}" ]; then
        echo "ERROR: GEMINI_API_KEY is not available in the environment."
        exit 1
    fi
    if [ -z "${GEMINI_MODEL:-}" ]; then
        echo "ERROR: GEMINI_MODEL is not configured."
        exit 1
    fi
    export UI_E2E_TIMEOUT="${UI_E2E_TIMEOUT:-300}"
else
    if ! command -v ollama >/dev/null 2>&1; then
        echo "ERROR: Ollama is not installed or not on PATH."
        exit 1
    fi

    if [ -z "${GEMMA_MODEL:-}" ]; then
        echo "ERROR: GEMMA_MODEL is not configured."
        exit 1
    fi

    if ! ollama list >/dev/null 2>&1; then
        echo "ERROR: Ollama is not running."
        exit 1
    fi

    export UI_E2E_TIMEOUT="${UI_E2E_TIMEOUT:-900}"
fi

mkdir -p .demo
SERVER_LOG=".demo/ui-e2e-server.log"
SERVER_PID=""

cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
        kill "$SERVER_PID" >/dev/null 2>&1 || true
        wait "$SERVER_PID" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT INT TERM

printf "\n"
echo "============================================================"
echo " v0.9 END-TO-END UI ACCEPTANCE"
echo " Model: $(printf "%s" "$MODE" | tr "[:lower:]" "[:upper:]")"
echo "============================================================"
echo

# 1. Real Streamlit server smoke check.
# This verifies the app entrypoint can boot as an actual Streamlit server.
PORT="${UI_E2E_PORT:-8765}"

".venv/bin/python" -m streamlit run ui/streamlit_app.py \
    --server.headless true \
    --server.port "$PORT" \
    --browser.gatherUsageStats false \
    >"$SERVER_LOG" 2>&1 &

SERVER_PID=$!

READY=0
COUNT=0
while [ "$COUNT" -lt 30 ]; do
    if curl -fsS "http://localhost:${PORT}/_stcore/health" >/dev/null 2>&1; then
        READY=1
        break
    fi

    if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
        echo "ERROR: Streamlit server exited during startup."
        echo "----- $SERVER_LOG -----"
        tail -100 "$SERVER_LOG" || true
        exit 1
    fi

    sleep 1
    COUNT=$((COUNT + 1))
done

if [ "$READY" -ne 1 ]; then
    echo "ERROR: Streamlit health endpoint did not become ready."
    echo "----- $SERVER_LOG -----"
    tail -100 "$SERVER_LOG" || true
    exit 1
fi

echo "✓ Streamlit server booted successfully"
echo "✓ Health endpoint responded"

# The live query tests below use Streamlit's official AppTest API to
# programmatically operate the UI and inspect its rendered structured output.
# This avoids brittle browser-coordinate automation while still executing
# ui/streamlit_app.py itself.
echo
echo "Running generalized healthcare queries through Streamlit UI..."
echo

set +e
".venv/bin/python" -m pytest -q -s tests/e2e/test_ui_workflow.py
STATUS=$?
set -e

echo
if [ "$STATUS" -eq 0 ]; then
    printf "\033[1;32m"
    echo "┌──────────────────────────────────────────────────────────┐"
    echo "│  ✓ v0.9 UI END-TO-END ACCEPTANCE: PASS                 │"
    printf "│  MODEL: %-47s │\n" "$(printf "%s" "$MODE" | tr "[:lower:]" "[:upper:]")"
    echo "└──────────────────────────────────────────────────────────┘"
    printf "\033[0m"
else
    printf "\033[1;31m"
    echo "┌──────────────────────────────────────────────────────────┐"
    echo "│  ✗ v0.9 UI END-TO-END ACCEPTANCE: FAIL                 │"
    echo "└──────────────────────────────────────────────────────────┘"
    printf "\033[0m"
    exit "$STATUS"
fi
