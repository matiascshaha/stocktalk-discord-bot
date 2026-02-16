"""Centralized parsing and resolution for test feature flags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}

VALID_TEST_MODES = {"local", "smoke", "strict"}
VALID_WEBULL_ENVS = {"paper", "production"}
VALID_AI_SCOPES = {"sample", "full"}

MODE_DEFAULTS = {
    "local": {
        "TEST_AI_LIVE": "0",
        "TEST_DISCORD_LIVE": "0",
        "TEST_WEBULL_READ": "0",
        "TEST_WEBULL_WRITE": "0",
        "TEST_WEBULL_ENV": "paper",
        "TEST_AI_SCOPE": "sample",
    },
    "smoke": {
        "TEST_AI_LIVE": "1",
        "TEST_DISCORD_LIVE": "1",
        "TEST_WEBULL_READ": "1",
        "TEST_WEBULL_WRITE": "0",
        "TEST_WEBULL_ENV": "production",
        "TEST_AI_SCOPE": "sample",
    },
    "strict": {
        "TEST_AI_LIVE": "1",
        "TEST_DISCORD_LIVE": "1",
        "TEST_WEBULL_READ": "1",
        "TEST_WEBULL_WRITE": "0",
        "TEST_WEBULL_ENV": "production",
        "TEST_AI_SCOPE": "sample",
    },
}


@dataclass(frozen=True)
class TestFlags:
    mode: str
    ai_live: bool
    discord_live: bool
    webull_read: bool
    webull_write: bool
    webull_env: str
    ai_scope: str
    ai_providers: str
    brokers: str

    @property
    def strict_external(self) -> bool:
        return self.mode == "strict"

    def to_env(self, base_env: Mapping[str, str] | None = None) -> Dict[str, str]:
        env = dict(base_env or {})
        env.update(
            {
                "TEST_MODE": self.mode,
                "TEST_AI_LIVE": _bool_to_env(self.ai_live),
                "TEST_DISCORD_LIVE": _bool_to_env(self.discord_live),
                "TEST_WEBULL_READ": _bool_to_env(self.webull_read),
                "TEST_WEBULL_WRITE": _bool_to_env(self.webull_write),
                "TEST_WEBULL_ENV": self.webull_env,
                "TEST_AI_SCOPE": self.ai_scope,
                "TEST_AI_PROVIDERS": self.ai_providers,
                "TEST_BROKERS": self.brokers,
            }
        )
        return env


def _parse_choice(name: str, raw_value: str, allowed: set[str]) -> str:
    value = raw_value.strip().lower()
    if value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"{name} must be one of: {allowed_text}. Got: {raw_value!r}")
    return value


def _parse_optional_bool(name: str, raw_value: str | None, default: bool) -> bool:
    if raw_value is None:
        return default
    value = raw_value.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ValueError(f"{name} must be 0/1 (or true/false). Got: {raw_value!r}")


def _bool_to_env(value: bool) -> str:
    return "1" if value else "0"


def resolve_test_flags(env: Mapping[str, str], *, default_mode: str = "local") -> TestFlags:
    mode_raw = env.get("TEST_MODE", default_mode)
    mode = _parse_choice("TEST_MODE", mode_raw, VALID_TEST_MODES)
    defaults = MODE_DEFAULTS[mode]

    ai_live = _parse_optional_bool("TEST_AI_LIVE", env.get("TEST_AI_LIVE"), defaults["TEST_AI_LIVE"] == "1")
    discord_live = _parse_optional_bool(
        "TEST_DISCORD_LIVE", env.get("TEST_DISCORD_LIVE"), defaults["TEST_DISCORD_LIVE"] == "1"
    )
    webull_read = _parse_optional_bool(
        "TEST_WEBULL_READ", env.get("TEST_WEBULL_READ"), defaults["TEST_WEBULL_READ"] == "1"
    )
    webull_write = _parse_optional_bool(
        "TEST_WEBULL_WRITE", env.get("TEST_WEBULL_WRITE"), defaults["TEST_WEBULL_WRITE"] == "1"
    )

    webull_env_raw = env.get("TEST_WEBULL_ENV", defaults["TEST_WEBULL_ENV"])
    webull_env = _parse_choice("TEST_WEBULL_ENV", webull_env_raw, VALID_WEBULL_ENVS)

    ai_scope_raw = env.get("TEST_AI_SCOPE", defaults["TEST_AI_SCOPE"])
    ai_scope = _parse_choice("TEST_AI_SCOPE", ai_scope_raw, VALID_AI_SCOPES)

    ai_providers = env.get("TEST_AI_PROVIDERS", "openai,anthropic,google")
    brokers = env.get("TEST_BROKERS", "webull")

    return TestFlags(
        mode=mode,
        ai_live=ai_live,
        discord_live=discord_live,
        webull_read=webull_read,
        webull_write=webull_write,
        webull_env=webull_env,
        ai_scope=ai_scope,
        ai_providers=ai_providers,
        brokers=brokers,
    )
