from types import SimpleNamespace

import pytest

from src.providers.parser_dispatch import UnsupportedProviderError, request_provider_completion


def _provider_config():
    return {
        "openai": {"model": "gpt-4o", "max_tokens": 128, "temperature": 0.2},
        "anthropic": {"model": "claude-sonnet-4-5", "max_tokens": 128, "temperature": 0.2},
        "google": {"model": "gemini-3-pro-preview", "temperature": 0.2},
    }


class _FakeOpenAIClient:
    def __init__(self, response_text: str):
        self.calls = []
        self.response_text = response_text
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.response_text)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _FakeAnthropicClient:
    def __init__(self, response_text: str):
        self.calls = []
        self.response_text = response_text
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(text=self.response_text)])


class _FakeGoogleClient:
    def __init__(self, response_text: str):
        self.calls = []
        self.response_text = response_text

    def generate_content(self, prompt):
        self.calls.append(prompt)
        return SimpleNamespace(text=self.response_text)


@pytest.mark.unit
def test_request_provider_completion_routes_openai():
    client = _FakeOpenAIClient('{"signals":[]}')
    result = request_provider_completion("openai", client, _provider_config(), "hello")
    assert result == '{"signals":[]}'
    assert len(client.calls) == 1
    assert "response_format" in client.calls[0]


@pytest.mark.unit
def test_request_provider_completion_routes_anthropic():
    client = _FakeAnthropicClient('{"signals":[]}')
    result = request_provider_completion("anthropic", client, _provider_config(), "hello")
    assert result == '{"signals":[]}'
    assert len(client.calls) == 1
    assert client.calls[0]["model"] == "claude-sonnet-4-5"


@pytest.mark.unit
def test_request_provider_completion_routes_google():
    client = _FakeGoogleClient('{"signals":[]}')
    result = request_provider_completion("google", client, _provider_config(), "hello")
    assert result == '{"signals":[]}'
    assert client.calls == ["hello"]


@pytest.mark.unit
def test_request_provider_completion_rejects_unknown_provider():
    with pytest.raises(UnsupportedProviderError):
        request_provider_completion("invalid", object(), _provider_config(), "hello")
