#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_DIR="$ROOT_DIR/.demo"
PID_FILE="$DEMO_DIR/streamlit.pid"
OLLAMA_PID_FILE="$DEMO_DIR/ollama.pid"

stop_pid_file() {
  local file="$1"
  local label="$2"

  if [[ ! -f "$file" ]]; then
    return
  fi

  local pid
  pid="$(cat "$file" 2>/dev/null || true)"

  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "Stopping $label (PID $pid)..."
    kill "$pid" || true

    for _ in {1..10}; do
      if ! kill -0 "$pid" 2>/dev/null; then
        break
      fi
      sleep 1
    done

    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" || true
    fi
  fi

  rm -f "$file"
}

stop_pid_file "$PID_FILE" "Streamlit demo"
stop_pid_file "$OLLAMA_PID_FILE" "Ollama started by demo script"

echo "Demo stopped."
