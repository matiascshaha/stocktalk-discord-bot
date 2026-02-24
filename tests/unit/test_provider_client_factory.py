import types
from unittest.mock import MagicMock

import pytest

import src.providers.client_factory as client_factory_module
from src.providers.client_factory import build_provider_client


pytestmark = [pytest.mark.unit]


def test_build_provider_client_returns_none_without_required_api_keys():
    assert build_provider_client("openai", {}, openai_api_key=None) is None
    assert build_provider_client("anthropic", {}, anthropic_api_key=None) is None
    assert build_provider_client("google", {"google": {"model": "x"}}, google_api_key=None) is None


def test_build_provider_client_creates_openai_client(monkeypatch):
    constructor = MagicMock(return_value="openai-client")
    monkeypatch.setattr(client_factory_module.openai, "OpenAI", constructor)

    client = build_provider_client("openai", {}, openai_api_key="key")

    assert client == "openai-client"
    constructor.assert_called_once_with(api_key="key")


def test_build_provider_client_creates_anthropic_client(monkeypatch):
    constructor = MagicMock(return_value="anthropic-client")
    monkeypatch.setattr(client_factory_module.anthropic, "Anthropic", constructor)

    client = build_provider_client("anthropic", {}, anthropic_api_key="key")

    assert client == "anthropic-client"
    constructor.assert_called_once_with(api_key="key")


def test_build_provider_client_creates_google_client(monkeypatch):
    fake_google_package = types.ModuleType("google")
    fake_genai_module = types.ModuleType("google.generativeai")
    fake_genai_module.configure = MagicMock()
    fake_genai_module.GenerativeModel = MagicMock(return_value="google-client")
    fake_google_package.generativeai = fake_genai_module

    monkeypatch.setitem(__import__("sys").modules, "google", fake_google_package)
    monkeypatch.setitem(__import__("sys").modules, "google.generativeai", fake_genai_module)

    client = build_provider_client(
        "google",
        {"google": {"model": "gemini-3-pro-preview"}},
        google_api_key="key",
    )

    assert client == "google-client"
    fake_genai_module.configure.assert_called_once_with(api_key="key")
    fake_genai_module.GenerativeModel.assert_called_once_with("gemini-3-pro-preview")


def test_build_provider_client_returns_none_for_unknown_provider():
    assert build_provider_client("unknown", {}, openai_api_key="key") is None
