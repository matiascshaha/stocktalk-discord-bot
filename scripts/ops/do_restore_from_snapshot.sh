#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Restore a Droplet from a snapshot.

Usage:
  ./scripts/ops/do_restore_from_snapshot.sh \
    --snapshot <snapshot-id-or-name> \
    --name <new-droplet-name> \
    --region <region> \
    --ssh-key <fingerprint-or-id> \
    [--tag <tag>] [--project <project-id>] [--size <slug>]

If --size is omitted, the cheapest available size in the region is used.
EOF
}

if ! command -v doctl >/dev/null 2>&1; then
  echo "error: doctl is required but not installed" >&2
  exit 1
fi

SNAPSHOT=""
NAME=""
REGION=""
SSH_KEY=""
TAG="stocktalk"
PROJECT_ID=""
SIZE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --snapshot) SNAPSHOT="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --region) REGION="${2:-}"; shift 2 ;;
    --ssh-key) SSH_KEY="${2:-}"; shift 2 ;;
    --tag) TAG="${2:-}"; shift 2 ;;
    --project) PROJECT_ID="${2:-}"; shift 2 ;;
    --size) SIZE="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${SNAPSHOT}" || -z "${NAME}" || -z "${REGION}" || -z "${SSH_KEY}" ]]; then
  echo "error: --snapshot, --name, --region, and --ssh-key are required" >&2
  usage
  exit 1
fi

if doctl compute droplet list --format Name --no-header | grep -Fxq "${NAME}"; then
  echo "error: droplet with name '${NAME}' already exists" >&2
  exit 1
fi

resolve_snapshot_id() {
  local input="$1"
  if [[ "${input}" =~ ^[0-9]+$ ]]; then
    echo "${input}"
    return 0
  fi

  doctl compute snapshot list --resource droplet --format ID,Name --no-header \
    | awk -v name="${input}" '$2 == name {print $1; exit}'
}

SNAPSHOT_ID="$(resolve_snapshot_id "${SNAPSHOT}")"
if [[ -z "${SNAPSHOT_ID}" ]]; then
  echo "error: snapshot not found: ${SNAPSHOT}" >&2
  exit 1
fi

if [[ -z "${SIZE}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SIZE="$("${SCRIPT_DIR}/do_select_cheapest_size.sh" "${REGION}")"
fi

echo "Restoring from snapshot ${SNAPSHOT_ID} into droplet '${NAME}' with size ${SIZE}" >&2

CREATE_OUTPUT="$(
  doctl compute droplet create "${NAME}" \
    --region "${REGION}" \
    --size "${SIZE}" \
    --image "${SNAPSHOT_ID}" \
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
