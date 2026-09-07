#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLUSTER_NAME="healthcare-agentic"
NAMESPACE="healthcare-ai"
IMAGE="gemini-healthcare-agentic-platform:v1.2-dev"
SERVICE="healthcare-ai-service"
PORT="8501"
PID_FILE="/tmp/gemini-healthcare-agentic-k8s-port-forward.pid"

cd "$ROOT_DIR"

echo "=== Beyond RAG Kubernetes Demo ==="

for command_name in docker kubectl kind curl; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "ERROR: $command_name is required."
    exit 1
  fi
done

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is not running."
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "ERROR: .env was not found."
  exit 1
fi

set -a
source .env
set +a

MODEL_PROVIDER="${1:-${MODEL_PROVIDER:-gemini}}"

if [ "$MODEL_PROVIDER" != "gemini" ]; then
  echo "ERROR: v1.2 local Kubernetes acceptance currently supports the Gemini path."
  echo "Use: ./scripts/demo-k8s.sh gemini"
  exit 1
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "ERROR: GEMINI_API_KEY is not configured in .env."
  exit 1
fi

if [ -z "${GEMINI_MODEL:-}" ]; then
  echo "ERROR: GEMINI_MODEL is not configured in .env."
  exit 1
fi

echo
echo "Model provider: $MODEL_PROVIDER"
echo "Gemini model:   $GEMINI_MODEL"
echo "Cluster:        $CLUSTER_NAME"
echo "Namespace:      $NAMESPACE"
echo "Image:          $IMAGE"

if ! kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  echo
  echo "Creating kind cluster..."
  kind create cluster --name "$CLUSTER_NAME"
else
  echo
  echo "Using existing kind cluster: $CLUSTER_NAME"
fi

kubectl config use-context "kind-$CLUSTER_NAME" >/dev/null

echo
echo "Building Docker image..."
docker build -t "$IMAGE" .

echo
echo "Loading image into kind..."
kind load docker-image "$IMAGE" --name "$CLUSTER_NAME"

echo
echo "Applying namespace..."
kubectl apply -f deployment/kubernetes/namespace.yaml

echo
echo "Applying non-sensitive configuration..."
kubectl apply -f deployment/kubernetes/configmap.yaml

echo
echo "Creating/updating Kubernetes secret from local environment..."
kubectl create secret generic healthcare-ai-secrets \
  --namespace "$NAMESPACE" \
  --from-literal=GEMINI_API_KEY="$GEMINI_API_KEY" \
  --dry-run=client \
  -o yaml | kubectl apply -f -

echo
echo "Applying workload..."
kubectl apply -f deployment/kubernetes/deployment.yaml
kubectl apply -f deployment/kubernetes/service.yaml

echo
echo "Waiting for rollout..."
kubectl rollout status deployment/healthcare-ai-app \
  --namespace "$NAMESPACE" \
  --timeout=180s

echo
echo "Restarting local port-forward..."

if [ -f "$PID_FILE" ]; then
  OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$OLD_PID" ]; then
    kill "$OLD_PID" >/dev/null 2>&1 || true
  fi
  rm -f "$PID_FILE"
fi

kubectl port-forward \
  service/"$SERVICE" \
  "$PORT:$PORT" \
  --namespace "$NAMESPACE" \
  >/tmp/gemini-healthcare-agentic-k8s-port-forward.log 2>&1 &

PORT_FORWARD_PID=$!
echo "$PORT_FORWARD_PID" > "$PID_FILE"

echo
echo "Waiting for Streamlit health endpoint..."

HEALTH_OK=0
ATTEMPT=1

while [ "$ATTEMPT" -le 30 ]; do
  if curl -fsS "http://localhost:$PORT/_stcore/health" >/dev/null 2>&1; then
    HEALTH_OK=1
    break
  fi

  sleep 2
  ATTEMPT=$((ATTEMPT + 1))
done

if [ "$HEALTH_OK" -ne 1 ]; then
  echo "ERROR: Application health endpoint did not become ready."
  echo
  kubectl get pods -n "$NAMESPACE"
  echo
  kubectl logs deployment/healthcare-ai-app -n "$NAMESPACE" --tail=50 || true
  exit 1
fi

echo
echo "Kubernetes demo is ready."
echo
echo "Application: http://localhost:$PORT"
echo "Health:      http://localhost:$PORT/_stcore/health"
echo
echo "Run:"
echo "  ./scripts/demo-k8s-status.sh"
echo
echo "Stop:"
echo "  ./scripts/demo-k8s-stop.sh"
