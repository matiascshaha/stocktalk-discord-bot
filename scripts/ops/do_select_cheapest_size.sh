#!/usr/bin/env bash
set -euo pipefail

# Prints the cheapest available Droplet size slug.
# Optional region filter:
#   ./scripts/ops/do_select_cheapest_size.sh nyc1

if ! command -v doctl >/dev/null 2>&1; then
  echo "error: doctl is required but not installed" >&2
  exit 1
fi

REGION="${1:-}"

JSON="$(doctl compute size list --output json)"

SLUG="$(
  python3 - "${REGION}" "${JSON}" <<'PY'
import json
import sys

region = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
raw = sys.argv[2] if len(sys.argv) > 2 else "[]"
sizes = json.loads(raw)

candidates = []
for size in sizes:
    if not bool(size.get("available", False)):
        continue
    if region:
        regions = size.get("regions") or []
        if region not in regions:
            continue

    slug = size.get("slug")
    if not slug:
        continue

    monthly = float(size.get("price_monthly", 0) or 0)
    hourly = float(size.get("price_hourly", 0) or 0)
    candidates.append((monthly, hourly, slug))

if not candidates:
    sys.exit(2)

candidates.sort(key=lambda row: (row[0], row[1], row[2]))
print(candidates[0][2])
PY
)"

if [[ -z "${SLUG}" ]]; then
  echo "error: could not resolve a cheapest size slug" >&2
  exit 1
fi

echo "${SLUG}"
