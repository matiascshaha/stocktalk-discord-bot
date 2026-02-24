# CI/CD Runbook

## Pipeline stages

1. Lint and static checks
2. Unit/integration tests
3. UI/E2E suites
4. Build/package
5. Deploy and smoke checks

## Failure triage sequence

1. Identify first failing stage.
2. Classify as infra, env, flaky test, or code regression.
3. Gather artifacts and logs.
4. Apply minimal fix and re-run impacted stages.

## Common failure signatures

| Signature | Likely cause | Fix pattern |
|---|---|---|
| Timeout in UI tests | env load/slowness | improve waits, stabilize data |
| Random auth failures | session/token race | fix fixture/auth bootstrap |
| Build only fails in CI | missing env/config | align local and CI env |

## Release safety

- Deploy behind feature flags where possible.
- Keep rollback path documented per service.
