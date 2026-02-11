from argparse import Namespace

from scripts.full_confidence import _build_env


def _args(**overrides):
    data = {
        "mode": "full",
        "include_webull_write": False,
        "ai_provider": None,
        "brokers": None,
        "webull_paper_required": False,
        "webull_smoke_paper_trade": False,
    }
    data.update(overrides)
    return Namespace(**data)


def _clear_runner_env(monkeypatch):
    keys = [
        "FULL_CONFIDENCE_REQUIRED",
        "RUN_LIVE_AI_TESTS",
        "RUN_LIVE_AI_PIPELINE_FULL",
        "RUN_DISCORD_LIVE_SMOKE",
        "RUN_WEBULL_READ_SMOKE",
        "RUN_WEBULL_WRITE_TESTS",
        "WEBULL_SMOKE_PAPER_TRADE",
        "WEBULL_PAPER_REQUIRED",
        "TEST_AI_PROVIDERS",
        "TEST_BROKERS",
        "AI_PROVIDER",
        "PAPER_TRADE",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_build_env_deterministic_profile(monkeypatch):
    _clear_runner_env(monkeypatch)
    env = _build_env(_args(mode="deterministic"))

    assert env["FULL_CONFIDENCE_REQUIRED"] == "0"
    assert env["RUN_LIVE_AI_TESTS"] == "0"
    assert env["RUN_DISCORD_LIVE_SMOKE"] == "0"
    assert env["RUN_WEBULL_READ_SMOKE"] == "0"
    assert env["RUN_WEBULL_WRITE_TESTS"] == "0"


def test_build_env_full_profile_defaults(monkeypatch):
    _clear_runner_env(monkeypatch)
    env = _build_env(_args(mode="full"))

    assert env["FULL_CONFIDENCE_REQUIRED"] == "1"
    assert env["RUN_LIVE_AI_TESTS"] == "1"
    assert env["RUN_DISCORD_LIVE_SMOKE"] == "1"
    assert env["RUN_WEBULL_READ_SMOKE"] == "1"
    assert env["RUN_WEBULL_WRITE_TESTS"] == "0"
    assert env["WEBULL_SMOKE_PAPER_TRADE"] == "0"


def test_build_env_full_profile_include_webull_write(monkeypatch):
    _clear_runner_env(monkeypatch)
    monkeypatch.setenv("PAPER_TRADE", "false")

    env = _build_env(_args(mode="full", include_webull_write=True))
    assert env["RUN_WEBULL_WRITE_TESTS"] == "1"
    assert env["WEBULL_SMOKE_PAPER_TRADE"] == "false"


def test_build_env_full_profile_force_webull_smoke_paper(monkeypatch):
    _clear_runner_env(monkeypatch)

    env = _build_env(
        _args(mode="full", include_webull_write=True, webull_smoke_paper_trade=True)
    )
    assert env["RUN_WEBULL_WRITE_TESTS"] == "1"
    assert env["WEBULL_SMOKE_PAPER_TRADE"] == "1"
