#!/usr/bin/env bash
set -euo pipefail

# Assumes your SSH key is already configured locally and authorized on the droplet.

if ! command -v doctl >/dev/null 2>&1; then
  echo "error: doctl is required but not installed" >&2
  exit 1
fi

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "usage: ./scripts/ops/do_ssh_vm.sh [droplet-id-or-name] [user] [remote-command]"
  exit 0
fi

DROPLET="${1:-stocktalk-vm}"
USER_NAME="${2:-root}"

REMOTE_CMD=""
if [[ $# -ge 3 ]]; then
  REMOTE_CMD="${*:3}"
fi

IP_ADDR="$(doctl compute droplet list --format ID,Name,PublicIPv4 --no-header \
  | awk -v target="${DROPLET}" '$1 == target || $2 == target {print $3; exit}')"

if [[ -z "${IP_ADDR}" || "${IP_ADDR}" == "<nil>" ]]; then
  echo "error: droplet not found or has no public IPv4: ${DROPLET}" >&2
  exit 1
fi

echo "Connecting to ${USER_NAME}@${IP_ADDR} (droplet: ${DROPLET})..." >&2

if [[ -n "${REMOTE_CMD}" ]]; then
  ssh -o StrictHostKeyChecking=accept-new "${USER_NAME}@${IP_ADDR}" "${REMOTE_CMD}"
else
  ssh -o StrictHostKeyChecking=accept-new "${USER_NAME}@${IP_ADDR}"
fi
