#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Power on a DigitalOcean Droplet by ID or name.

Usage:
  ./scripts/ops/do_power_on_vm.sh --droplet <id-or-name>
EOF
}

if ! command -v doctl >/dev/null 2>&1; then
  echo "error: doctl is required but not installed" >&2
  exit 1
fi

TARGET=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --droplet) TARGET="${2:-}"; shift 2 ;;
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

DROPLET_ID="$(resolve_droplet_id "${TARGET}")"
if [[ -z "${DROPLET_ID}" ]]; then
  echo "error: droplet not found: ${TARGET}" >&2
  exit 1
fi

doctl compute droplet-action power-on "${DROPLET_ID}" --wait
echo "Powered on droplet ${DROPLET_ID}"
