"""Provider/broker test matrix helpers.

These helpers keep test discovery extensible as new AI providers or broker
integrations are added.
"""

import os
from typing import List


PLACEHOLDER_KEY_MARKERS = (
    "your_",
    "replace",
    "example",
    "changeme",
    "<",
    ">",
)


def parse_csv_env(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def enabled_ai_providers() -> List[str]:
    return parse_csv_env("TEST_AI_PROVIDERS", "openai,anthropic,google")


def enabled_brokers() -> List[str]:
    return parse_csv_env("TEST_BROKERS", "webull")


def ai_provider_key_env(provider: str) -> str:
    mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }
    return mapping.get(provider, "")


def has_real_credential(value: str) -> bool:
    candidate = (value or "").strip()
    if not candidate:
        return False
    lowered = candidate.lower()
    if lowered.endswith("here"):
        return False
    return not any(marker in lowered for marker in PLACEHOLDER_KEY_MARKERS)


def ai_provider_has_credentials(provider: str) -> bool:
    env_key = ai_provider_key_env(provider)
    return bool(env_key and has_real_credential(os.getenv(env_key, "")))
