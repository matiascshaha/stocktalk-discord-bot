"""Provider-agnostic parser completion dispatch."""

from typing import Any, Dict, Optional

from src.providers.anthropic.parser_client import (
    request_parser_completion as request_anthropic_parser_completion,
)
from src.providers.google.parser_client import (
    request_parser_completion as request_google_parser_completion,
)
from src.providers.openai.parser_client import (
    request_parser_completion as request_openai_parser_completion,
)


class UnsupportedProviderError(ValueError):
    """Raised when parser completion is requested for an unsupported provider."""


def request_provider_completion(
    provider: str,
    client: Any,
    config: Dict[str, Any],
    prompt: str,
    model_override: Optional[str] = None,
    max_tokens_override: Optional[int] = None,
    temperature_override: Optional[float] = None,
) -> str:
    normalized_provider = (provider or "").lower().strip()

    if normalized_provider == "openai":
        openai_config = config["openai"]
        model = model_override or openai_config["model"]
        max_tokens = max_tokens_override if max_tokens_override is not None else openai_config["max_tokens"]
        temperature = temperature_override if temperature_override is not None else openai_config["temperature"]
        return request_openai_parser_completion(
            client=client,
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    if normalized_provider == "anthropic":
        anthropic_config = config["anthropic"]
        model = model_override or anthropic_config["model"]
        max_tokens = max_tokens_override if max_tokens_override is not None else anthropic_config["max_tokens"]
        temperature = temperature_override if temperature_override is not None else anthropic_config["temperature"]
        return request_anthropic_parser_completion(
            client=client,
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    if normalized_provider == "google":
        return request_google_parser_completion(client=client, prompt=prompt)

    raise UnsupportedProviderError(f"Unsupported provider: {provider}")
