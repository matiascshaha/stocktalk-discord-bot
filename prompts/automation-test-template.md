# Automation Test Prompt Template

Test objective:
<What user/system behavior to validate>

Framework:
<Playwright or Robot Framework>

Required process:
1. Find existing similar tests and shared fixtures/resources.
2. Reuse established selector and wait patterns.
3. Implement test with deterministic data assumptions.
4. Execute targeted test command.
5. Report artifacts and failures with actionable triage notes.

Must follow:
- `docs/test-standards.md`
- `docs/selector-policy.md`
- `docs/playwright-patterns.md` or `docs/robot-patterns.md`
