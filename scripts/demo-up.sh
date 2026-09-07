#!/usr/bin/env bash

set -e

NAMESPACE="healthcare-ai"
SERVICE="healthcare-ai-service"

echo "Making service publicly accessible..."

kubectl patch service "$SERVICE" \
  -n "$NAMESPACE" \
  -p '{"spec":{"type":"LoadBalancer"}}'

echo "Waiting for GCP external IP..."

while true; do
  EXTERNAL_IP=$(kubectl get service "$SERVICE" \
    -n "$NAMESPACE" \
    -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)

  if [ -n "$EXTERNAL_IP" ]; then
    break
  fi

  sleep 5
done

echo
echo "=========================================="
echo "Healthcare AI Demo"
echo "=========================================="
echo "URL: http://${EXTERNAL_IP}:8501"
echo
echo "Health check:"

curl -fsS "http://${EXTERNAL_IP}:8501/_stcore/health" || true

echo
echo "=========================================="
