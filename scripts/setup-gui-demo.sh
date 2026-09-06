#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== GUI demo setup =="

if [[ ! -f requirements.txt ]]; then
  echo "ERROR: requirements.txt not found. Run this from the repository."
  exit 1
fi

if ! grep -Eq '^[[:space:]]*streamlit([<=>!~ ].*)?$' requirements.txt; then
  printf '\nstreamlit\n' >> requirements.txt
  echo "Added streamlit to requirements.txt"
else
  echo "streamlit already present in requirements.txt"
fi

chmod +x scripts/demo-local.sh scripts/demo-stop.sh scripts/setup-gui-demo.sh

if [[ -d .venv ]]; then
  echo "Installing/updating dependencies in active project environment..."
  python -m pip install -r requirements.txt
else
  echo "No .venv directory found."
  echo "Create/activate your virtual environment, then run:"
  echo "  python -m pip install -r requirements.txt"
fi

echo
echo "Setup complete."
echo "Run Gemini demo: ./scripts/demo-local.sh gemini"
echo "Run Gemma demo:  ./scripts/demo-local.sh gemma"
