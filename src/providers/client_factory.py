"""Provider client initialization helpers."""

from typing import Any, Dict, Optional

import anthropic
import openai


def build_provider_client(
    provider: str,
    config: Dict[str, Any],
    anthropic_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    google_api_key: Optional[str] = None,
) -> Optional[Any]:
    normalized_provider = (provider or "").lower().strip()

    if normalized_provider == "anthropic":
        if not anthropic_api_key:
            return None
        return anthropic.Anthropic(api_key=anthropic_api_key)

    if normalized_provider == "openai":
        if not openai_api_key:
            return None
        return openai.OpenAI(api_key=openai_api_key)

    if normalized_provider == "google":
        if not google_api_key:
            return None
        import google.generativeai as genai

        genai.configure(api_key=google_api_key)
        model_name = config["google"]["model"]
        return genai.GenerativeModel(model_name)

    return None
