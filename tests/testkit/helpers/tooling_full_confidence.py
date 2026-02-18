from argparse import Namespace


RUNNER_ENV_KEYS = [
    "TEST_MODE",
    "TEST_AI_LIVE",
    "TEST_AI_SCOPE",
    "TEST_DISCORD_LIVE",
    "TEST_WEBULL_READ",
    "TEST_WEBULL_WRITE",
    "TEST_WEBULL_ENV",
    "TEST_AI_PROVIDERS",
    "TEST_BROKERS",
    "AI_PROVIDER",
]


def make_full_confidence_args(**overrides):
    data = {
        "mode": "strict",
        "ai_live": None,
        "discord_live": None,
        "webull_read": None,
        "webull_write": None,
        "webull_env": None,
        "ai_scope": None,
        "ai_provider": None,
        "brokers": None,
    }
    data.update(overrides)
    return Namespace(**data)


def clear_runner_env(monkeypatch):
    for key in RUNNER_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
