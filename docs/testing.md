# Testing Strategy

## Test pyramid

- Unit tests: fast logic validation.
- Integration tests: service boundaries and contracts.
- E2E/UI tests: user-critical paths only.

## Test layout policy

- `tests/unit`, `tests/contract`, `tests/integration`, `tests/smoke` are application behavior tests.
- `tests/tooling` is reserved for tests of test runners and support scripts.
- Shared test setup belongs in `conftest.py` or `tests/support/`, not in test modules.

## Test module purity

- Test modules should contain tests only.
- Do not define helper classes/functions in `test_*.py` files.
- Move fakes/factories/payload builders into `tests/support/`.
- Enforced in CI by `python -m scripts.check_test_file_purity`.

## Quality gates

- No merge if lint/typecheck fails.
- No merge if impacted tests fail.
- Flaky test mitigation required before re-enabling unstable suites.

## Flaky test policy

1. Detect and tag flaky tests.
2. Capture trace/log/screenshot evidence.
3. Triage root cause within agreed SLA.
4. Quarantine only with linked issue and owner.

## Coverage

Track coverage trends; do not optimize for vanity percentages.

## Manual happy path

For a super simple end-to-end manual check (run app, send one Discord message, verify local output + Webull paper order attempt), use `docs/manual-testing.md`.
