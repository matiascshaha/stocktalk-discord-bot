#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Control the stocktalk systemd service on a remote VM via SSH.

Usage:
  ./scripts/ops/do_app_control.sh --host <ip-or-hostname> --action <start|stop|restart|status|logs|enable|disable>
    [--user <user>] [--identity <private-key-path>] [--port <ssh-port>]

Notes:
  - Single-user only (no auto-trying users).
  - Forces IdentitiesOnly so SSH uses exactly the key you specify.
EOF
}

HOST=""
ACTION=""
USER_NAME="root"
IDENTITY_FILE="${HOME}/.ssh/id_ed25519_stocktalk"
SSH_PORT="22"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="${2:-}"; shift 2 ;;
    --action) ACTION="${2:-}"; shift 2 ;;
    --user) USER_NAME="${2:-}"; shift 2 ;;
    --identity) IDENTITY_FILE="${2:-}"; shift 2 ;;
    --port) SSH_PORT="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${HOST}" || -z "${ACTION}" ]]; then
  echo "error: --host and --action are required" >&2
  usage
  exit 1
fi

case "${ACTION}" in
  start|stop|restart|status|logs|enable|disable) ;;
  *)
    echo "error: invalid action '${ACTION}'" >&2
    usage
    exit 1
    ;;
esac

if [[ ! "${SSH_PORT}" =~ ^[0-9]+$ ]]; then
  echo "error: --port must be numeric" >&2
  exit 1
fi

# Expand ~
IDENTITY_FILE="${IDENTITY_FILE/#\~/${HOME}}"

if [[ ! -r "${IDENTITY_FILE}" ]]; then
  echo "error: identity file is not readable: ${IDENTITY_FILE}" >&2
  exit 1
fi

# Simple reachability check (bash built-in TCP)
# If blocked/firewalled you'll get a fast, clear error instead of "mystery" SSH failure.
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

REMOTE_CMD=""
if [[ "${ACTION}" == "logs" ]]; then
  REMOTE_CMD="sudo journalctl -u stocktalk -n 200 --no-pager"
elif [[ "${ACTION}" == "status" ]]; then
  REMOTE_CMD="sudo systemctl status stocktalk --no-pager"
elif [[ "${ACTION}" == "enable" ]]; then
  REMOTE_CMD="sudo systemctl enable stocktalk && sudo systemctl status stocktalk --no-pager"
elif [[ "${ACTION}" == "disable" ]]; then
  REMOTE_CMD="sudo systemctl disable stocktalk && sudo systemctl stop stocktalk && sudo systemctl status stocktalk --no-pager || true"
else
  REMOTE_CMD="sudo systemctl ${ACTION} stocktalk && sudo systemctl status stocktalk --no-pager"
fi

# Preflight: verify auth works before running sudo/systemctl (better error messages)
if ! ssh "${SSH_OPTS[@]}" "${USER_NAME}@${HOST}" "true" >/dev/null 2>&1; then
  err="$(ssh "${SSH_OPTS[@]}" "${USER_NAME}@${HOST}" "true" 2>&1 || true)"
  echo "error: SSH auth/connect failed." >&2
  echo "Host: ${HOST}:${SSH_PORT}" >&2
  echo "User: ${USER_NAME}" >&2
  echo "Key:  ${IDENTITY_FILE}" >&2
  echo "" >&2
  echo "${err}" >&2
  echo "" >&2
  echo "Tip: if you see 'REMOTE HOST IDENTIFICATION HAS CHANGED', run:" >&2
  echo "  ssh-keygen -R ${HOST}" >&2
  echo "" >&2
  echo "Exact command:" >&2
  echo "  ssh ${SSH_OPTS[*]} ${USER_NAME}@${HOST} true" >&2
  exit 1
fi

# Run command
ssh "${SSH_OPTS[@]}" "${USER_NAME}@${HOST}" "${REMOTE_CMD}"
