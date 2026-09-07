#!/usr/bin/env bash

set -e

echo "Changing service back to ClusterIP..."

kubectl patch service healthcare-ai-service \
  -n healthcare-ai \
  -p '{"spec":{"type":"ClusterIP"}}'

echo "Public demo LoadBalancer removed."
