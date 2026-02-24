#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Control the stocktalk systemd service on a remote VM via SSH.

Usage:
  ./scripts/ops/do_app_control.sh --host <ip-or-hostname> --action <start|stop|restart|status|logs> [--user <user>]
EOF
}

HOST=""
ACTION=""
USER_NAME="root"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="${2:-}"; shift 2 ;;
    --action) ACTION="${2:-}"; shift 2 ;;
    --user) USER_NAME="${2:-}"; shift 2 ;;
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
  start|stop|restart|status|logs) ;;
  *)
    echo "error: invalid action '${ACTION}'" >&2
    usage
    exit 1
    ;;
esac

SSH_OPTS=(
  -o StrictHostKeyChecking=accept-new
  -o ConnectTimeout=10
)

REMOTE_CMD=""
if [[ "${ACTION}" == "logs" ]]; then
  REMOTE_CMD="sudo journalctl -u stocktalk -n 200 --no-pager"
elif [[ "${ACTION}" == "status" ]]; then
  REMOTE_CMD="sudo systemctl status stocktalk --no-pager"
else
  REMOTE_CMD="sudo systemctl ${ACTION} stocktalk && sudo systemctl status stocktalk --no-pager"
fi

ssh "${SSH_OPTS[@]}" "${USER_NAME}@${HOST}" "${REMOTE_CMD}"
