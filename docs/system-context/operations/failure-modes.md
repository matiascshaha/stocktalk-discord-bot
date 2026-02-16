# Failure Modes

## Metadata

- Owner: `team-name`
- Last reviewed: `YYYY-MM-DD`

## Known failure patterns

| Symptom | Likely causes | Where to look first | Mitigation | Permanent fix path |
|---|---|---|---|---|
| replace-me | replace-me | logs/metrics/system | replace-me | replace-me |

## Fast triage checklist

1. Confirm scope (single tenant/user/region vs global).
2. Confirm first failure timestamp and correlated deploy/config change.
3. Trace request/event IDs across boundaries.
4. Validate upstream contract assumptions and payload shape.
5. Verify rollback/fallback options before broad changes.
