import os
import types
from unittest.mock import MagicMock

import pytest

from src.providers.client_factory import build_provider_client


pytestmark = [pytest.mark.unit]
RUN_OPTIONAL_PROVIDER_TESTS = os.getenv("RUN_OPTIONAL_PROVIDER_TESTS") == "1"
OPTIONAL_PROVIDER_TESTS_REASON = "Optional provider tests are disabled. Set RUN_OPTIONAL_PROVIDER_TESTS=1 to run."


def test_build_provider_client_returns_none_without_required_api_keys():
    assert build_provider_client("openai", {}, openai_api_key=None) is None
    assert build_provider_client("anthropic", {}, anthropic_api_key=None) is None
    assert build_provider_client("google", {"google": {"model": "x"}}, google_api_key=None) is None


def test_build_provider_client_creates_openai_client(monkeypatch):
    fake_openai_module = types.SimpleNamespace(OpenAI=MagicMock(return_value="openai-client"))
    import_module = MagicMock(return_value=fake_openai_module)
    monkeypatch.setattr("src.providers.client_factory.importlib.import_module", import_module)

    constructor = MagicMock(return_value="openai-client")
    fake_openai_module.OpenAI = constructor

    client = build_provider_client("openai", {}, openai_api_key="key")

    assert client == "openai-client"
    import_module.assert_called_once_with("openai")
    constructor.assert_called_once_with(api_key="key")


@pytest.mark.skipif(not RUN_OPTIONAL_PROVIDER_TESTS, reason=OPTIONAL_PROVIDER_TESTS_REASON)
def test_build_provider_client_creates_anthropic_client(monkeypatch):
    fake_anthropic_module = types.SimpleNamespace(Anthropic=MagicMock(return_value="anthropic-client"))
    import_module = MagicMock(return_value=fake_anthropic_module)
    monkeypatch.setattr("src.providers.client_factory.importlib.import_module", import_module)

    constructor = MagicMock(return_value="anthropic-client")
    fake_anthropic_module.Anthropic = constructor

    client = build_provider_client("anthropic", {}, anthropic_api_key="key")

    assert client == "anthropic-client"
    import_module.assert_called_once_with("anthropic")
    constructor.assert_called_once_with(api_key="key")


@pytest.mark.skipif(not RUN_OPTIONAL_PROVIDER_TESTS, reason=OPTIONAL_PROVIDER_TESTS_REASON)
def test_build_provider_client_creates_google_client(monkeypatch):
    fake_genai_module = types.ModuleType("google.generativeai")
    fake_genai_module.configure = MagicMock()
    fake_genai_module.GenerativeModel = MagicMock(return_value="google-client")

    import_module = MagicMock(return_value=fake_genai_module)
    monkeypatch.setattr("src.providers.client_factory.importlib.import_module", import_module)

    client = build_provider_client(
        "google",
        {"google": {"model": "gemini-3-pro-preview"}},
        google_api_key="key",
    )

    assert client == "google-client"
    import_module.assert_called_once_with("google.generativeai")
    fake_genai_module.configure.assert_called_once_with(api_key="key")
    fake_genai_module.GenerativeModel.assert_called_once_with("gemini-3-pro-preview")


def test_build_provider_client_returns_none_for_unknown_provider():
    assert build_provider_client("unknown", {}, openai_api_key="key") is None
