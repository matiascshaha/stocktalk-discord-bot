#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Create a DigitalOcean Droplet using the cheapest available size in a region.

Usage:
  ./scripts/ops/do_create_droplet.sh --name <name> --region <region> --ssh-key <fingerprint-or-id> [options]

Options:
  --name <name>             Droplet name (required)
  --region <region>         Region slug, e.g. nyc1 (required)
  --ssh-key <value>         SSH key fingerprint or numeric ID (required)
  --image <image>           Image slug (default: ubuntu-24-04-x64)
  --tag <tag>               Tag for resource targeting (default: stocktalk)
  --project <project-id>    Optional project ID to assign resource
EOF
}

if ! command -v doctl >/dev/null 2>&1; then
  echo "error: doctl is required but not installed" >&2
  exit 1
fi

NAME=""
REGION=""
SSH_KEY=""
IMAGE="ubuntu-24-04-x64"
TAG="stocktalk"
PROJECT_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="${2:-}"; shift 2 ;;
    --region) REGION="${2:-}"; shift 2 ;;
    --ssh-key) SSH_KEY="${2:-}"; shift 2 ;;
    --image) IMAGE="${2:-}"; shift 2 ;;
    --tag) TAG="${2:-}"; shift 2 ;;
    --project) PROJECT_ID="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${NAME}" || -z "${REGION}" || -z "${SSH_KEY}" ]]; then
  echo "error: --name, --region, and --ssh-key are required" >&2
  usage
  exit 1
fi

if doctl compute droplet list --format Name --no-header | grep -Fxq "${NAME}"; then
  echo "error: droplet with name '${NAME}' already exists" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIZE_SLUG="$("${SCRIPT_DIR}/do_select_cheapest_size.sh" "${REGION}")"

echo "Using cheapest available size in ${REGION}: ${SIZE_SLUG}" >&2

CREATE_OUTPUT="$(
  doctl compute droplet create "${NAME}" \
    --region "${REGION}" \
    --size "${SIZE_SLUG}" \
    --image "${IMAGE}" \
    --ssh-keys "${SSH_KEY}" \
    --enable-monitoring \
    --tag-names "${TAG}" \
    --wait \
    --format ID,Name,PublicIPv4,Status,SizeSlug,Image \
    --no-header
)"

echo "${CREATE_OUTPUT}"

DROPLET_ID="$(awk 'NR==1{print $1}' <<<"${CREATE_OUTPUT}")"

if [[ -n "${PROJECT_ID}" && -n "${DROPLET_ID}" ]]; then
  doctl projects resources assign "${PROJECT_ID}" --resource "do:droplet:${DROPLET_ID}" >/dev/null
  echo "Assigned droplet ${DROPLET_ID} to project ${PROJECT_ID}" >&2
fi
