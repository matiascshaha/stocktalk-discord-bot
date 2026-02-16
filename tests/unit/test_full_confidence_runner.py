from argparse import Namespace

from scripts.quality.run_confidence_suite import _build_env


def _args(**overrides):
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


def _clear_runner_env(monkeypatch):
    keys = [
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
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_build_env_local_defaults(monkeypatch):
    _clear_runner_env(monkeypatch)
    env = _build_env(_args(mode="local"))

    assert env["TEST_MODE"] == "local"
    assert env["TEST_AI_LIVE"] == "0"
    assert env["TEST_DISCORD_LIVE"] == "0"
    assert env["TEST_WEBULL_READ"] == "0"
    assert env["TEST_WEBULL_WRITE"] == "0"
    assert env["TEST_WEBULL_ENV"] == "paper"
    assert env["TEST_AI_SCOPE"] == "sample"


def test_build_env_strict_defaults(monkeypatch):
    _clear_runner_env(monkeypatch)
    env = _build_env(_args(mode="strict"))

    assert env["TEST_MODE"] == "strict"
    assert env["TEST_AI_LIVE"] == "1"
    assert env["TEST_DISCORD_LIVE"] == "1"
    assert env["TEST_WEBULL_READ"] == "1"
    assert env["TEST_WEBULL_WRITE"] == "0"
    assert env["TEST_WEBULL_ENV"] == "production"
    assert env["TEST_AI_SCOPE"] == "sample"


def test_build_env_explicit_overrides(monkeypatch):
    _clear_runner_env(monkeypatch)

    env = _build_env(
        _args(
            mode="strict",
            ai_live="1",
            discord_live="0",
            webull_read="1",
            webull_write="1",
            webull_env="paper",
            ai_scope="full",
        )
    )

    assert env["TEST_AI_LIVE"] == "1"
    assert env["TEST_DISCORD_LIVE"] == "0"
    assert env["TEST_WEBULL_READ"] == "1"
    assert env["TEST_WEBULL_WRITE"] == "1"
    assert env["TEST_WEBULL_ENV"] == "paper"
    assert env["TEST_AI_SCOPE"] == "full"


def test_build_env_ai_provider_override(monkeypatch):
    _clear_runner_env(monkeypatch)
    env = _build_env(_args(ai_provider="openai"))
    assert env["AI_PROVIDER"] == "openai"
    assert env["TEST_AI_PROVIDERS"] == "openai"
