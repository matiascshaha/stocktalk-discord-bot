"""Trading provider registry and validation helpers."""

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional


DEFAULT_EXECUTION_PROVIDER = "webull"
DEFAULT_QUOTE_PROVIDER = "auto"


@dataclass(frozen=True)
class ProviderCapabilities:
    execution: bool
    quotes: bool


PROVIDER_CAPABILITIES: Dict[str, ProviderCapabilities] = {
    "webull": ProviderCapabilities(execution=True, quotes=True),
    "yahoo": ProviderCapabilities(execution=False, quotes=True),
    "public": ProviderCapabilities(execution=False, quotes=False),
}


def resolve_execution_provider_name(trading_config: Mapping[str, Any]) -> str:
    raw_value = _first_non_empty(
        trading_config.get("execution_provider"),
        DEFAULT_EXECUTION_PROVIDER,
    )
    return _normalize_provider_name(raw_value, default=DEFAULT_EXECUTION_PROVIDER)


def resolve_quote_provider_name(
    trading_config: Mapping[str, Any],
    execution_provider: Optional[str] = None,
) -> str:
    raw_value = _first_non_empty(
        trading_config.get("quote_provider"),
        DEFAULT_QUOTE_PROVIDER,
    )
    quote_provider = _normalize_provider_name(raw_value, default=DEFAULT_QUOTE_PROVIDER)
    if quote_provider == DEFAULT_QUOTE_PROVIDER:
        return execution_provider or resolve_execution_provider_name(trading_config)
    return quote_provider


def validate_provider_split(execution_provider: str, quote_provider: str) -> List[str]:
    errors: List[str] = []

    execution_capabilities = PROVIDER_CAPABILITIES.get(execution_provider)
    quote_capabilities = PROVIDER_CAPABILITIES.get(quote_provider)

    if execution_capabilities is None:
        errors.append(
            f"Unsupported trading execution provider '{execution_provider}'. "
            f"Supported providers: {', '.join(sorted(PROVIDER_CAPABILITIES))}"
        )
    elif not execution_capabilities.execution:
        errors.append(
            f"Execution provider '{execution_provider}' is configured but not implemented."
        )

    if quote_capabilities is None:
        errors.append(
            f"Unsupported trading quote provider '{quote_provider}'. "
            f"Supported providers: {', '.join(sorted(PROVIDER_CAPABILITIES))}"
        )
    elif not quote_capabilities.quotes:
        errors.append(
            f"Quote provider '{quote_provider}' is configured but not implemented."
        )

    return errors


def _normalize_provider_name(raw_value: Any, default: str) -> str:
    if raw_value is None:
        return default
    normalized = str(raw_value).strip().lower()
    if not normalized:
        return default
    return normalized


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None
