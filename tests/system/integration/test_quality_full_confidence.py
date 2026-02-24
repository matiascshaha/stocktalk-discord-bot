import pytest

from scripts.quality.run_confidence_suite import _build_env
from tests.support.tooling.full_confidence import clear_runner_env, make_full_confidence_args


pytestmark = [pytest.mark.integration, pytest.mark.system]


def test_build_env_local_defaults(monkeypatch):
    clear_runner_env(monkeypatch)
    env = _build_env(make_full_confidence_args(mode="local"))

    assert env["TEST_MODE"] == "local"
    assert env["TEST_AI_LIVE"] == "0"
    assert env["TEST_DISCORD_LIVE"] == "0"
    assert env["TEST_WEBULL_READ"] == "0"
    assert env["TEST_WEBULL_WRITE"] == "0"
    assert env["TEST_WEBULL_ENV"] == "paper"
    assert env["TEST_AI_SCOPE"] == "sample"


def test_build_env_strict_defaults(monkeypatch):
    clear_runner_env(monkeypatch)
    env = _build_env(make_full_confidence_args(mode="strict"))

    assert env["TEST_MODE"] == "strict"
    assert env["TEST_AI_LIVE"] == "1"
    assert env["TEST_DISCORD_LIVE"] == "1"
    assert env["TEST_WEBULL_READ"] == "1"
    assert env["TEST_WEBULL_WRITE"] == "0"
    assert env["TEST_WEBULL_ENV"] == "production"
    assert env["TEST_AI_SCOPE"] == "sample"


def test_build_env_explicit_overrides(monkeypatch):
    clear_runner_env(monkeypatch)

    env = _build_env(
        make_full_confidence_args(
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
    clear_runner_env(monkeypatch)
    env = _build_env(make_full_confidence_args(ai_provider="openai"))
    assert env["AI_PROVIDER"] == "openai"
    assert env["TEST_AI_PROVIDERS"] == "openai"
