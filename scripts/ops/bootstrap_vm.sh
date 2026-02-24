#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Bootstrap a Ubuntu VM for stocktalk Docker runtime.
Run this script on the VM after cloning the repository.

Usage:
  sudo ./scripts/ops/bootstrap_vm.sh [--start-now] [--install-market-hours-timers]
EOF
}

START_NOW="0"
INSTALL_TIMERS="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
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

if [[ "${EUID}" -ne 0 ]]; then
  echo "error: run as root (use sudo)" >&2
  exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "error: this bootstrap script currently supports apt-based systems only" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "Installing Docker runtime packages..."
apt-get update
apt-get install -y --no-install-recommends docker.io docker-compose-plugin ca-certificates curl rsync

systemctl enable --now docker

mkdir -p /opt/stocktalk
rsync -a --delete --exclude '.git' "${REPO_ROOT}/" /opt/stocktalk/
mkdir -p /opt/stocktalk/data

if [[ ! -f /opt/stocktalk/.env && -f /opt/stocktalk/.env.example ]]; then
  cp /opt/stocktalk/.env.example /opt/stocktalk/.env
  echo "Created /opt/stocktalk/.env from .env.example (fill secrets before starting app)." >&2
fi

install -m 0644 "${REPO_ROOT}/deploy/systemd/stocktalk.service" /etc/systemd/system/stocktalk.service

if [[ "${INSTALL_TIMERS}" == "1" ]]; then
  install -m 0644 "${REPO_ROOT}/deploy/systemd/stocktalk-start.service" /etc/systemd/system/stocktalk-start.service
  install -m 0644 "${REPO_ROOT}/deploy/systemd/stocktalk-stop.service" /etc/systemd/system/stocktalk-stop.service
  install -m 0644 "${REPO_ROOT}/deploy/systemd/stocktalk-start.timer" /etc/systemd/system/stocktalk-start.timer
  install -m 0644 "${REPO_ROOT}/deploy/systemd/stocktalk-stop.timer" /etc/systemd/system/stocktalk-stop.timer
fi

systemctl daemon-reload
systemctl enable stocktalk.service

if [[ "${INSTALL_TIMERS}" == "1" ]]; then
  systemctl enable stocktalk-start.timer stocktalk-stop.timer
fi

if [[ "${START_NOW}" == "1" ]]; then
  systemctl start stocktalk.service
fi

echo "Bootstrap complete."
echo "Service status:"
systemctl status stocktalk --no-pager || true
