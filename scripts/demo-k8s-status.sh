#!/bin/bash
set -e

CLUSTER_NAME="healthcare-agentic"
NAMESPACE="healthcare-ai"
PORT="8501"
PID_FILE="/tmp/gemini-healthcare-agentic-k8s-port-forward.pid"

echo "=== Kubernetes Demo Status ==="

echo
echo "Cluster:"
if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  echo "$CLUSTER_NAME: running"
else
  echo "$CLUSTER_NAME: not found"
  exit 0
fi

echo
echo "Workloads:"
kubectl get deployment,pods,service -n "$NAMESPACE" -o wide 2>/dev/null || \
  echo "No healthcare-ai workloads found."

echo
echo "Pod restarts:"
kubectl get pods -n "$NAMESPACE" \
  -o custom-columns='NAME:.metadata.name,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,STATUS:.status.phase' \
  2>/dev/null || true

echo
echo "Port-forward:"
if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE" 2>/dev/null || true)"

  if [ -n "$PID" ] && kill -0 "$PID" >/dev/null 2>&1; then
    echo "running (PID $PID)"
  else
    echo "not running"
  fi
else
  echo "not running"
fi

echo
echo "Health:"
if curl -fsS "http://localhost:$PORT/_stcore/health" 2>/dev/null; then
  echo
else
  echo "unavailable"
fi
