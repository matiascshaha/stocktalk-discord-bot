# Cursor Integration Map

This folder extends existing repository conventions, it does not replace them.

## Source of truth

- `AGENTS.md` defines global operating policy.
- `docs/` contains durable standards and runbooks.
- `scripts/` contains operational helpers.
- `mcp/` contains provider-agnostic MCP notes/templates.

## Cursor-specific layer

- `.cursor/rules/*.mdc`: scoped rule routing by file type/domain.
- `.cursorignore`: excludes files from Cursor context and `@` references.
- `.cursorindexingignore`: excludes files from indexing only.
- `.cursor/mcp.json`: Cursor project-level MCP server config.

## Practical rule

When editing rules, update matching docs in `docs/` if policy changed.
Keep this layer as routing and enforcement, not duplicated knowledge.
