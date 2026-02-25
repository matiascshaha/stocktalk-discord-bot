"""Provider client initialization helpers."""

import importlib
from typing import Any, Dict, Optional


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
        anthropic_module = _import_optional_dependency("anthropic")
        return anthropic_module.Anthropic(api_key=anthropic_api_key)

    if normalized_provider == "openai":
        if not openai_api_key:
            return None
        openai_module = _import_optional_dependency("openai")
        return openai_module.OpenAI(api_key=openai_api_key)

    if normalized_provider == "google":
        if not google_api_key:
            return None
        genai = _import_optional_dependency("google.generativeai")

        genai.configure(api_key=google_api_key)
        model_name = config["google"]["model"]
        return genai.GenerativeModel(model_name)

    return None


def _import_optional_dependency(module_name: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise RuntimeError(
            f"Missing optional dependency '{module_name}'. Install it to use this AI provider."
        ) from exc
