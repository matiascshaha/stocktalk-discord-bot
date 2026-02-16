# Dependency Matrix

## Metadata

- Owner: `team-name`
- Last reviewed: `YYYY-MM-DD`

## Inbound dependencies (they depend on us)

| Consumer system | Dependency type | Contract/spec | Criticality | Break impact | Owner |
|---|---|---|---|---|---|
| replace-me | API/Event/UI | link-to-contract | high/med/low | replace-me | team-name |

## Outbound dependencies (we depend on them)

| Provider system | Dependency type | Contract/spec | Criticality | Failure fallback | Owner |
|---|---|---|---|---|---|
| replace-me | API/Event/DB | link-to-contract | high/med/low | replace-me | team-name |

## Blast radius notes

- If `<system>` degrades, `<capability>` is impacted: replace-me
- If `<contract>` changes, impacted consumers: replace-me

## Change-risk checklist

1. Which upstream and downstream systems are impacted?
2. Are contract tests or compatibility checks available?
3. Is there a rollback or feature-flag path?
