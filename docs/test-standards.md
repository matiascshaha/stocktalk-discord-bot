# UI Test Automation Standards

## Scope

Applies to Robot Framework and Playwright test suites.

## Test design

- One assertion objective per test where practical.
- Prefer stable business-level assertions over visual noise.
- Avoid cross-test state leakage.

## Data strategy

- Use deterministic test data fixtures.
- Avoid relying on production-like mutable data.

## Retry strategy

- Retries are allowed only for known transient failures.
- Do not hide deterministic failures with retries.

## Evidence requirements

For failed tests, collect:
- Logs
- Screenshots
- Traces/videos when applicable
- Network/debug artifacts for API-dependent failures

## Naming and tagging

- Consistent tag taxonomy: `smoke`, `regression`, `critical`, `flaky`, `api-dependent`.
