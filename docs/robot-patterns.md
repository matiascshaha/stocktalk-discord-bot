# Robot Framework Patterns

## Resource design

- Keep reusable keywords in resource files.
- Separate UI, API, and environment helper keywords.

## Keyword style

- Use domain language and clear preconditions.
- Keep keyword side effects explicit.

## Variable management

- Centralize environment variables in variable files.
- Avoid hardcoding environment-specific URLs or credentials.

## Execution hygiene

- Tag tests consistently.
- Run focused suites/tests during development.
- Capture `output.xml`, `log.html`, and `report.html` for every CI run.
