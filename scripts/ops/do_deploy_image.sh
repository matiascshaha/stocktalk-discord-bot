#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Deploy a prebuilt container image tag to the stocktalk VM.

Usage:
  ./scripts/ops/do_deploy_image.sh --host <ip-or-hostname> --image-tag <tag>
    [--image-repository <repo>] [--container-name <name>] [--no-restart]
    [--user <user>] [--identity <private-key-path>] [--port <ssh-port>]

Notes:
  - Writes /opt/stocktalk/.env.runtime on the VM.
  - Pulls IMAGE_REPOSITORY:IMAGE_TAG on the VM.
  - Restarts stocktalk.service by default.
EOF
}

HOST=""
IMAGE_TAG=""
IMAGE_REPOSITORY=""
CONTAINER_NAME=""
USER_NAME="root"
IDENTITY_FILE="${HOME}/.ssh/id_ed25519_stocktalk"
SSH_PORT="22"
RESTART_SERVICE="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="${2:-}"; shift 2 ;;
    --image-tag) IMAGE_TAG="${2:-}"; shift 2 ;;
    --image-repository) IMAGE_REPOSITORY="${2:-}"; shift 2 ;;
    --container-name) CONTAINER_NAME="${2:-}"; shift 2 ;;
    --user) USER_NAME="${2:-}"; shift 2 ;;
    --identity) IDENTITY_FILE="${2:-}"; shift 2 ;;
    --port) SSH_PORT="${2:-}"; shift 2 ;;
    --no-restart) RESTART_SERVICE="0"; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${HOST}" || -z "${IMAGE_TAG}" ]]; then
  echo "error: --host and --image-tag are required" >&2
  usage
  exit 1
fi

if [[ ! "${SSH_PORT}" =~ ^[0-9]+$ ]]; then
  echo "error: --port must be numeric" >&2
  exit 1
fi

if [[ ! "${IMAGE_TAG}" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "error: --image-tag may only contain letters, numbers, dot, underscore, and dash" >&2
  exit 1
fi

if [[ -n "${IMAGE_REPOSITORY}" && ! "${IMAGE_REPOSITORY}" =~ ^[A-Za-z0-9._/-]+$ ]]; then
  echo "error: --image-repository may only contain letters, numbers, slash, dot, underscore, and dash" >&2
  exit 1
fi

if [[ -n "${CONTAINER_NAME}" && ! "${CONTAINER_NAME}" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "error: --container-name may only contain letters, numbers, dot, underscore, and dash" >&2
  exit 1
fi

IDENTITY_FILE="${IDENTITY_FILE/#\~/${HOME}}"

if [[ ! -r "${IDENTITY_FILE}" ]]; then
  echo "error: identity file is not readable: ${IDENTITY_FILE}" >&2
  exit 1
fi

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

quoted_args=(
  "$(printf '%q' "${IMAGE_TAG}")"
  "$(printf '%q' "${IMAGE_REPOSITORY}")"
  "$(printf '%q' "${CONTAINER_NAME}")"
  "$(printf '%q' "${RESTART_SERVICE}")"
)

ssh "${SSH_OPTS[@]}" "${USER_NAME}@${HOST}" \
  "sudo bash -s -- ${quoted_args[*]}" <<'REMOTE'
set -euo pipefail

IMAGE_TAG="${1:-}"
INPUT_IMAGE_REPOSITORY="${2:-}"
INPUT_CONTAINER_NAME="${3:-}"
RESTART_SERVICE="${4:-1}"
RUNTIME_ENV_FILE="/opt/stocktalk/.env.runtime"

current_image_repository=""
current_container_name="stocktalk-bot"

if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
  while IFS='=' read -r key value; do
    case "${key}" in
      IMAGE_REPOSITORY) current_image_repository="${value}" ;;
      CONTAINER_NAME) current_container_name="${value}" ;;
    esac
  done < "${RUNTIME_ENV_FILE}"
fi

image_repository="${INPUT_IMAGE_REPOSITORY:-${current_image_repository}}"
container_name="${INPUT_CONTAINER_NAME:-${current_container_name}}"

if [[ -z "${image_repository}" ]]; then
  echo "error: IMAGE_REPOSITORY is not set. Pass --image-repository the first time." >&2
  exit 1
fi

install -d -m 0755 /opt/stocktalk

cat > "${RUNTIME_ENV_FILE}" <<EOF
IMAGE_REPOSITORY=${image_repository}
IMAGE_TAG=${IMAGE_TAG}
CONTAINER_NAME=${container_name}
EOF

/usr/bin/docker pull "${image_repository}:${IMAGE_TAG}"

if [[ "${RESTART_SERVICE}" == "1" ]]; then
  /usr/bin/systemctl daemon-reload
  /usr/bin/systemctl restart stocktalk.service
  /usr/bin/systemctl status stocktalk.service --no-pager || true
  /usr/bin/journalctl -u stocktalk.service -n 80 --no-pager || true
fi
REMOTE
