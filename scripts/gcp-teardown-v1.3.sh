#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-gemini-healthcare-agentic}"
CLUSTER_NAME="${CLUSTER_NAME:-healthcare-agentic-gke}"
ZONE="${ZONE:-us-central1-a}"
NAMESPACE="${NAMESPACE:-healthcare-ai}"
SERVICE_NAME="${SERVICE_NAME:-healthcare-ai-service}"

echo "======================================================================"
echo "Gemini Healthcare Agentic Platform - Google Cloud teardown"
echo "======================================================================"
echo "Project:   ${PROJECT_ID}"
echo "Cluster:   ${CLUSTER_NAME}"
echo "Zone:      ${ZONE}"
echo "Namespace: ${NAMESPACE}"
echo
echo "WILL DELETE:"
echo "  - GKE cluster ${CLUSTER_NAME}"
echo "  - Cluster nodes/workloads"
echo "  - Managed OpenTelemetry components inside the cluster"
echo
echo "WILL KEEP:"
echo "  - Google Cloud project"
echo "  - Enabled APIs"
echo "  - Artifact Registry and container images"
echo "  - Git/local source code"
echo "  - GitHub branches/tags/history"
echo "======================================================================"
echo

command -v gcloud >/dev/null 2>&1 || {
  echo "ERROR: gcloud is not installed or not in PATH."
  exit 1
}

gcloud config set project "${PROJECT_ID}" >/dev/null

echo "Checking whether the GKE cluster exists..."
if ! gcloud container clusters describe "${CLUSTER_NAME}" \
  --zone="${ZONE}" \
  --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo
  echo "Cluster ${CLUSTER_NAME} does not exist."
  echo "Nothing to delete."
  echo
  gcloud container clusters list --project="${PROJECT_ID}" || true
  exit 0
fi

echo "Cluster found."
echo

if command -v kubectl >/dev/null 2>&1; then
  echo "Refreshing kubectl credentials..."
  if gcloud container clusters get-credentials "${CLUSTER_NAME}" \
      --zone="${ZONE}" \
      --project="${PROJECT_ID}" >/dev/null 2>&1; then

    if kubectl get svc "${SERVICE_NAME}" -n "${NAMESPACE}" >/dev/null 2>&1; then
      CURRENT_TYPE="$(kubectl get svc "${SERVICE_NAME}" -n "${NAMESPACE}" \
        -o jsonpath='{.spec.type}' 2>/dev/null || true)"

      echo "Current service type: ${CURRENT_TYPE:-unknown}"

      if [[ "${CURRENT_TYPE:-}" == "LoadBalancer" ]]; then
        echo "Switching ${SERVICE_NAME} back to ClusterIP..."
        kubectl patch svc "${SERVICE_NAME}" \
          -n "${NAMESPACE}" \
          -p '{"spec":{"type":"ClusterIP"}}'
        echo "Public LoadBalancer exposure removed."
      else
        echo "Service is not a LoadBalancer. No public service change needed."
      fi
    else
      echo "Application service not found. Continuing."
    fi
  else
    echo "Could not refresh kubectl credentials. Continuing."
  fi
else
  echo "kubectl is not available. Continuing."
fi

echo
echo "FINAL CONFIRMATION"
echo "This will permanently delete:"
echo "  ${CLUSTER_NAME} (${ZONE})"
echo
read -r -p "Type DELETE to continue: " CONFIRM

if [[ "${CONFIRM}" != "DELETE" ]]; then
  echo "Cancelled. No cluster deletion was performed."
  exit 0
fi

echo
echo "Deleting GKE cluster..."
gcloud container clusters delete "${CLUSTER_NAME}" \
  --zone="${ZONE}" \
  --project="${PROJECT_ID}" \
  --quiet

echo
echo "======================================================================"
echo "Teardown complete."
echo "======================================================================"

echo
echo "Remaining GKE clusters:"
gcloud container clusters list --project="${PROJECT_ID}" || true

echo
echo "Artifact Registry repositories are intentionally preserved:"
gcloud artifacts repositories list \
  --project="${PROJECT_ID}" \
  --location=us-central1 \
  --format="table(name,format,location)" 2>/dev/null || true

echo
echo "Remaining forwarding rules (inspection only; not deleting):"
gcloud compute forwarding-rules list \
  --project="${PROJECT_ID}" \
  --format="table(name,region,IPAddress,target)" 2>/dev/null || true

echo
echo "Reserved external IP addresses (inspection only; not deleting):"
gcloud compute addresses list \
  --project="${PROJECT_ID}" \
  --format="table(name,address,status,region)" 2>/dev/null || true

echo
echo "IMPORTANT:"
echo "  - Enabled APIs were NOT disabled."
echo "  - Artifact Registry was NOT deleted."
echo "  - Git/local files were NOT modified."
echo "  - Cloud Trace/Logging history was NOT deleted."
echo
echo "When you resume: recreate the GKE cluster, enable Managed OpenTelemetry,"
echo "apply deployment/kubernetes manifests, and deploy v1.3-dev or rebuild it."
