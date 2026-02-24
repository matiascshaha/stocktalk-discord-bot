# Test Standards

## Purpose

Define a simple, high-discipline testing standard that delivers strong regression confidence with maintainable test code.

## Testing Philosophy

- Keep strategy simple and explicit.
- Keep design and implementation details rigorous.
- Test behavior and contracts, not private internals.
- Prefer fast deterministic feedback first, then broader confidence layers.

## Strategy Playbook

Use this order when planning test scope for a change:

1. Identify risk: what failure would hurt users, money, data, or trust.
2. Identify blast radius: where the change crosses module or service boundaries.
3. Choose the cheapest layer that can prove the behavior.
4. Add only the smallest additional tests needed for confidence.
5. Remove redundant or low-value tests when they duplicate higher-value coverage.

## What To Test

- Business-critical flows and high-impact user journeys.
- Boundary contracts between modules, services, providers, and brokers.
- High-churn code paths and previously fragile areas.
- Failure paths, validation logic, and recovery behavior.
- Performance and load behavior where latency/throughput are product constraints.

## What Not To Test

- Trivial pass-through code with no branching risk when already covered indirectly.
- Duplicative assertions across multiple layers for the same behavior.
- Vendor/internal framework behavior already guaranteed upstream.
- Brittle implementation details that block refactors without reducing risk.

## Balancing Simplicity and Coverage

- Keep most coverage in unit and contract/integration tests.
- Keep e2e/smoke small, critical-path only, and stable.
- Use live/write tests as gated confidence checks, not default local blockers.
- Measure confidence by escaped-defect reduction and signal quality, not raw test count.

## Hard Problem Simplification

When a test problem feels complex, simplify in this sequence:

1. Move logic behind a clear seam and test it deterministically.
2. Replace broad e2e assertions with narrow contract assertions where possible.
3. Standardize fixtures/factories so setup is reusable and readable.
4. Freeze nondeterminism (time, randomness, external state) at test boundaries.
5. Split large scenario tests into focused behavior checks with explicit intent.

## Test Design and Test Code Standards

- Each test verifies one clear behavior.
- Names are descriptive: `test_<behavior>`.
- Test structure is explicit: setup, action, assertion.
- Assertions explain intent and expected outcome.
- Test code follows production standards: modular, readable, and organized.
- Shared helpers live in dedicated support locations, not inside test modules.

## Effort Allocation Across Layers and Teams

- Unit: owned by feature implementers; fastest regression net for logic.
- Contract/Integration: co-owned at integration boundaries; verify interfaces and orchestration.
- E2E/Smoke: owned by product/system quality scope; protect critical user outcomes.
- Performance/Load: owned by system/performance scope for capacity and latency risk.
- Security/compliance tests: owned by relevant domain owners where applicable.

Use ownership by boundary, not by tooling. Teams can use different frameworks if contracts and quality gates stay consistent.

## Regression Automation Model

- Maintain a small, always-on deterministic blocking suite.
- Run broader confidence suites in CI and scheduled checks.
- Keep live/write suites opt-in or policy-gated with explicit environment controls.
- Every flaky test requires triage, owner, and resolution path.

## Quality Gates

- Block merge on deterministic failures in changed scope.
- Require lint/typecheck/static checks before merge.
- Require targeted regression tests for touched risk areas.
- Require clear failure evidence for external/live failures.

## Failure Evidence

When reporting failures, include:

- exact command
- failing assertion and logs
- environment/config flags
- relevant artifacts (trace, screenshot, request/response evidence)

## Internal References

- Project test structure: `docs/testing.md`
- Project matrix and commands: `tests/README.md`
- Run commands and operational steps: `docs/runbook.md`
- Test module purity guard: `scripts/check_test_file_purity.py`
