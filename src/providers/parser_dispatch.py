"""Provider-agnostic parser completion dispatch."""

from typing import Any, Dict

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
) -> str:
    normalized_provider = (provider or "").lower().strip()

    if normalized_provider == "openai":
        openai_config = config["openai"]
        return request_openai_parser_completion(
            client=client,
            model=openai_config["model"],
            prompt=prompt,
            max_tokens=openai_config["max_tokens"],
            temperature=openai_config["temperature"],
        )

    if normalized_provider == "anthropic":
        anthropic_config = config["anthropic"]
        return request_anthropic_parser_completion(
            client=client,
            model=anthropic_config["model"],
            prompt=prompt,
            max_tokens=anthropic_config["max_tokens"],
            temperature=anthropic_config["temperature"],
        )

    if normalized_provider == "google":
        return request_google_parser_completion(client=client, prompt=prompt)

    raise UnsupportedProviderError(f"Unsupported provider: {provider}")
