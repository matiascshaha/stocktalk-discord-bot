# MCP Integration Notes

Use MCP to connect AI tooling to external systems with a consistent interface.

## Suggested first integrations

- GitHub (issues, PRs, code context)
- CI provider logs and workflows
- Documentation/wiki sources

## Principles

- Prefer read-only by default.
- Require explicit approval for write actions.
- Log tool actions for auditing.

## Setup

1. Configure servers in `mcp/servers.example.json`.
2. Connect your AI client to MCP servers.
3. Test retrieval-only flows before enabling write operations.
