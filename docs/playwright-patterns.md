# Playwright Patterns

## Locator strategy

Priority order:
1. `getByRole`
2. `getByLabel`
3. `getByTestId`
4. CSS/XPath only as last resort

## Wait strategy

- Prefer built-in auto-waiting.
- Avoid raw sleeps except during diagnostics.

## Fixtures

- Centralize auth/session setup in fixtures.
- Keep test files focused on scenario logic.

## Network and API hooks

- Use route mocking sparingly and explicitly.
- Validate both UI behavior and key request outcomes.

## Debugging

- Use trace viewer and screenshot/video artifacts for triage.
- Capture reproducible steps in failure issues.
