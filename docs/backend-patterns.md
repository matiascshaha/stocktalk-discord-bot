# Backend Service Patterns

## API design

- Define request/response contracts explicitly.
- Validate inputs at boundaries.
- Return structured errors with machine-readable codes.

## Reliability

- Timeouts and retries must be explicit.
- Idempotency for retryable write operations.

## Observability

- Logs include correlation IDs and key dimensions.
- Emit metrics on latency, errors, and saturation.

## Testing

- Contract tests for external dependencies.
- Integration tests for persistence and messaging boundaries.
