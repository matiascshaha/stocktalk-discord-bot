#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Stop Droplet billing by snapshotting and deleting the Droplet.
This is the "not billed anymore" path for compute.

Usage:
  ./scripts/ops/do_stop_billing.sh --droplet <id-or-name> [--snapshot-name <name>]
EOF
}

if ! command -v doctl >/dev/null 2>&1; then
  echo "error: doctl is required but not installed" >&2
  exit 1
fi

TARGET=""
SNAPSHOT_NAME=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --droplet) TARGET="${2:-}"; shift 2 ;;
    --snapshot-name) SNAPSHOT_NAME="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${TARGET}" ]]; then
  echo "error: --droplet is required" >&2
  usage
  exit 1
fi

resolve_droplet_id() {
  local input="$1"
  if [[ "${input}" =~ ^[0-9]+$ ]]; then
    echo "${input}"
    return 0
  fi

  doctl compute droplet list --format ID,Name --no-header \
    | awk -v name="${input}" '$2 == name {print $1; exit}'
}

resolve_droplet_name() {
  local input="$1"
  if [[ "${input}" =~ ^[0-9]+$ ]]; then
    doctl compute droplet get "${input}" --format Name --no-header
    return 0
  fi
  echo "${input}"
}

DROPLET_ID="$(resolve_droplet_id "${TARGET}")"
if [[ -z "${DROPLET_ID}" ]]; then
  echo "error: droplet not found: ${TARGET}" >&2
  exit 1
fi

DROPLET_NAME="$(resolve_droplet_name "${TARGET}")"
if [[ -z "${SNAPSHOT_NAME}" ]]; then
  SNAPSHOT_NAME="stocktalk-${DROPLET_NAME}-$(date +%Y%m%d-%H%M%S)"
fi

echo "Creating snapshot '${SNAPSHOT_NAME}' from droplet ${DROPLET_ID}..." >&2
doctl compute droplet-action snapshot "${DROPLET_ID}" --snapshot-name "${SNAPSHOT_NAME}" --wait

SNAPSHOT_ID="$(
  doctl compute snapshot list --resource droplet --format ID,Name --no-header \
    | awk -v n="${SNAPSHOT_NAME}" '$2 == n {print $1; exit}'
)"

if [[ -z "${SNAPSHOT_ID}" ]]; then
  echo "error: snapshot created but could not resolve snapshot id for '${SNAPSHOT_NAME}'" >&2
  echo "aborting droplet deletion for safety" >&2
  exit 1
fi

echo "Snapshot complete: ${SNAPSHOT_ID} (${SNAPSHOT_NAME})" >&2
echo "Deleting droplet ${DROPLET_ID} to stop compute billing..." >&2
doctl compute droplet delete "${DROPLET_ID}" --force

echo "Done."
echo "Snapshot ID: ${SNAPSHOT_ID}"
echo "Snapshot Name: ${SNAPSHOT_NAME}"
