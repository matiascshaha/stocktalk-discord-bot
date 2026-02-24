#!/usr/bin/env bash
# Thin wrapper around scripts/bootstrap/project_setup.py to keep setup logic in one place.

set -euo pipefail

if command -v python3.11 >/dev/null 2>&1; then
  exec python3.11 scripts/bootstrap/project_setup.py
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/bootstrap/project_setup.py
fi

if command -v python >/dev/null 2>&1; then
  exec python scripts/bootstrap/project_setup.py
fi

echo "ERROR: Python 3.11.x is required and was not found in PATH."
exit 1
