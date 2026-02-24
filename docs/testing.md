# Testing Structure

## Current Layout

```text
tests/
  brokers/
    webull/
      contract/
      smoke/
  channels/
    discord/
      integration/
      smoke/
  data/
  parser/
    contract/
    smoke/
  support/
    cases/
    factories/
    fakes/
    payloads/
    tooling/
  system/
    integration/
  unit/
```

## Placement Rules

- `tests/unit/`: deterministic unit-level checks.
- `tests/parser/`: parser contract + parser smoke/live checks.
- `tests/channels/discord/`: Discord integration flow + Discord live smoke.
- `tests/brokers/webull/`: Webull contract checks + Webull live/read/write smoke.
- `tests/system/integration/`: cross-domain quality/confidence integration checks.
- `tests/support/`: reusable fakes/factories/helpers/tooling support.
- `tests/data/`: reusable static test data fixtures.

## Markers and Default Selection

- Marker taxonomy is defined in `pytest.ini`.
- `pytest` defaults to deterministic scope with `-m "not live and not write"`.
- `--strict-markers` is enabled; undeclared markers fail collection.

## Purity and Reuse Rules

- `test_*.py` modules should contain tests only.
- Shared setup goes in `conftest.py`.
- Shared helpers belong in `tests/support/`.
- Enforced by `python -m scripts.check_test_file_purity`.

## References

- Detailed strategy and command matrix: `tests/README.md`
- Manual end-to-end check: `docs/manual-testing.md`
