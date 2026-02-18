def parser_provider_config() -> dict[str, dict[str, str | int | float]]:
    return {
        "openai": {"model": "gpt-4o", "max_tokens": 128, "temperature": 0.2},
        "anthropic": {"model": "claude-sonnet-4-5", "max_tokens": 128, "temperature": 0.2},
        "google": {"model": "gemini-3-pro-preview", "temperature": 0.2},
    }
