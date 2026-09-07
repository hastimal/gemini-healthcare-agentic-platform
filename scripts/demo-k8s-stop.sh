#!/bin/bash
set -e

CLUSTER_NAME="healthcare-agentic"
NAMESPACE="healthcare-ai"
PID_FILE="/tmp/gemini-healthcare-agentic-k8s-port-forward.pid"

echo "=== Stopping Kubernetes Demo ==="

if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE" 2>/dev/null || true)"

  if [ -n "$PID" ]; then
    kill "$PID" >/dev/null 2>&1 || true
  fi

  rm -f "$PID_FILE"
  echo "Port-forward stopped."
else
  echo "No managed port-forward found."
fi

if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  kubectl config use-context "kind-$CLUSTER_NAME" >/dev/null 2>&1 || true

  if kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    kubectl delete namespace "$NAMESPACE"
    echo "Namespace deleted: $NAMESPACE"
  else
    echo "Namespace not present: $NAMESPACE"
  fi

  echo "kind cluster retained: $CLUSTER_NAME"
else
  echo "kind cluster not found."
fi
