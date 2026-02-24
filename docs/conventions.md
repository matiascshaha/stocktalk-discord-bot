# Engineering Conventions

## Branch and PR strategy

- Branch naming: `feature/<name>`, `fix/<name>`, `chore/<name>`
- PR title format: `[area] concise summary`
- After the first push for a branch, open a PR immediately and enable auto-merge.
- Keep auto-merge enabled for that PR as new commits are pushed.
- Auto-merge is configured on the PR, not on `git push`.
- Standard command: `gh pr merge --auto --squash <pr-number>`
- Always check PR mergeability/conflicts before enabling auto-merge.
- If conflicts exist, ask the requester how each conflict should be resolved before applying conflict edits.

## Coding standards

- Keep functions small and single-purpose.
- Prefer explicit naming over short aliases.
- Add comments only when logic is non-obvious.

## Design and organization principles

- Place code intentionally in the most relevant module, class, or function; do not dump code into convenient but unrelated locations.
- Favor clear modularity at function, class, file, and folder levels with explicit responsibilities.
- Prefer folder-based organization once a domain grows beyond a handful of files; avoid large flat directories when grouping improves navigation.
- Think about likely reuse before adding new code: extract shared behavior when it improves clarity and maintainability, but avoid premature abstraction.
- Keep functions and classes easy to understand; refactor when a unit grows too long, handles multiple responsibilities, or becomes hard to reason about.
- When deciding whether to split a file/module, weigh trade-offs (discoverability, coupling, testability, change frequency, and cognitive load) and choose the simplest maintainable structure.
- Use language features and patterns (functions, classes, inheritance, decorators, etc.) when they clearly improve readability, reuse, and API clarity.
- Follow language and ecosystem standards and idioms so code remains predictable and easy for others to work with.

## Provider integration layout

- Provider-specific implementation belongs in `src/providers/<provider>/`.
- Split provider modules by purpose:
  - `*_contract.py` for immutable schemas/response formats.
  - `*_client.py` for request execution and transport-level parsing.
  - optional mapper/adapter modules for conversion into internal models.
- Domain orchestrators (for example `AIParser`) should depend on provider entry points, not inline provider protocol details.

## API and contract rules

- Preserve backward compatibility unless a breaking change is approved.
- Update schema docs/tests with contract changes.

## Error handling and observability

- Return actionable errors.
- Emit logs with request/task correlation IDs.

## Review checklist

- Behavior is covered by tests.
- Risky paths include rollback notes.
- Code placement is intentional, and modularity trade-offs are justified (split/extract vs keep together).
- Folder structure remains coherent for the domain, and related artifacts are grouped predictably.
- Docs updated when behavior changes.
