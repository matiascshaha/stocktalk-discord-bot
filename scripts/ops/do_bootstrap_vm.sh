#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Bootstrap a remote VM for stocktalk in one command from your local machine.

Usage:
  ./scripts/ops/do_bootstrap_vm.sh --host <ip-or-hostname>
    [--user <user>] [--identity <private-key-path>] [--port <ssh-port>]
    [--start-now] [--install-market-hours-timers]

Notes:
  - Syncs current local repo to /tmp/stocktalk-bootstrap-src on the remote VM.
  - Then runs scripts/ops/bootstrap_vm.sh on the remote VM.
  - Uses IdentitiesOnly so SSH uses exactly the key you specify.
EOF
}

HOST=""
USER_NAME="root"
IDENTITY_FILE="${HOME}/.ssh/id_ed25519_stocktalk"
SSH_PORT="22"
START_NOW="0"
INSTALL_TIMERS="0"
REMOTE_DIR="/tmp/stocktalk-bootstrap-src"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="${2:-}"; shift 2 ;;
    --user) USER_NAME="${2:-}"; shift 2 ;;
    --identity) IDENTITY_FILE="${2:-}"; shift 2 ;;
    --port) SSH_PORT="${2:-}"; shift 2 ;;
    --start-now) START_NOW="1"; shift ;;
    --install-market-hours-timers) INSTALL_TIMERS="1"; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${HOST}" ]]; then
  echo "error: --host is required" >&2
  usage
  exit 1
fi

if [[ ! "${SSH_PORT}" =~ ^[0-9]+$ ]]; then
  echo "error: --port must be numeric" >&2
  exit 1
fi

IDENTITY_FILE="${IDENTITY_FILE/#\~/${HOME}}"

if [[ ! -r "${IDENTITY_FILE}" ]]; then
  echo "error: identity file is not readable: ${IDENTITY_FILE}" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Simple reachability check (bash built-in TCP)
if ! (exec 3<>"/dev/tcp/${HOST}/${SSH_PORT}") 2>/dev/null; then
  echo "error: cannot reach ${HOST}:${SSH_PORT} (firewall, wrong IP, or SSH not listening)" >&2
  exit 1
fi
exec 3>&- 3<&-

BATCH_MODE="${BATCH_MODE:-0}"
SSH_OPTS=(
  -o StrictHostKeyChecking=accept-new
  -o ConnectTimeout=10
  -o IdentitiesOnly=yes
  -i "${IDENTITY_FILE}"
  -p "${SSH_PORT}"
)

if [[ "${BATCH_MODE}" == "1" ]]; then
  SSH_OPTS+=(-o BatchMode=yes)
fi

# Validate auth early for clearer errors.
if ! ssh "${SSH_OPTS[@]}" "${USER_NAME}@${HOST}" "true" >/dev/null 2>&1; then
  err="$(ssh "${SSH_OPTS[@]}" "${USER_NAME}@${HOST}" "true" 2>&1 || true)"
  echo "error: SSH auth/connect failed." >&2
  echo "Host: ${HOST}:${SSH_PORT}" >&2
  echo "User: ${USER_NAME}" >&2
  echo "Key:  ${IDENTITY_FILE}" >&2
  echo "" >&2
  echo "${err}" >&2
  exit 1
fi

BOOTSTRAP_FLAGS=()
if [[ "${START_NOW}" == "1" ]]; then
  BOOTSTRAP_FLAGS+=(--start-now)
fi
if [[ "${INSTALL_TIMERS}" == "1" ]]; then
  BOOTSTRAP_FLAGS+=(--install-market-hours-timers)
fi

RSYNC_SSH_CMD=(
  ssh
  -o StrictHostKeyChecking=accept-new
  -o ConnectTimeout=10
  -o IdentitiesOnly=yes
  -i "${IDENTITY_FILE}"
  -p "${SSH_PORT}"
)

if [[ "${BATCH_MODE}" == "1" ]]; then
  RSYNC_SSH_CMD+=(-o BatchMode=yes)
fi

ssh "${SSH_OPTS[@]}" "${USER_NAME}@${HOST}" "mkdir -p '${REMOTE_DIR}'"

rsync -az --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '.env' \
  -e "${RSYNC_SSH_CMD[*]}" \
  "${REPO_ROOT}/" "${USER_NAME}@${HOST}:${REMOTE_DIR}/"

ssh "${SSH_OPTS[@]}" "${USER_NAME}@${HOST}" \
  "cd '${REMOTE_DIR}' && ./scripts/ops/bootstrap_vm.sh ${BOOTSTRAP_FLAGS[*]}"

