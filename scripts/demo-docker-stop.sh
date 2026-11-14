#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Stopping local healthcare observability stack..."
docker compose down
echo "Gemini Healthcare Agentic Platform local stack stopped."
