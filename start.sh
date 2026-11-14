#!/usr/bin/env bash
set -e

# Disable interactive ADK telemetry prompt
adk telemetry disable || true

# Start ADK Web UI on 8080 in background
adk web --host=0.0.0.0 --port=8080 agents &
ADK_PID=$!

# Trap SIGTERM and SIGINT to stop ADK
trap "kill -TERM $ADK_PID 2>/dev/null || true" SIGTERM SIGINT

# Start Streamlit foreground
python -m streamlit run ui/streamlit_app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true
