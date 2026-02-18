import pytest

from src.providers.parser_dispatch import UnsupportedProviderError, request_provider_completion
from tests.testkit.doubles.ai_clients import CapturingOpenAIClient, FakeAnthropicClient, FakeGoogleClient
from tests.testkit.helpers.provider_configs import parser_provider_config


@pytest.mark.unit
def test_request_provider_completion_routes_openai():
    client = CapturingOpenAIClient('{"signals":[]}')
    result = request_provider_completion("openai", client, parser_provider_config(), "hello")
    assert result == '{"signals":[]}'
    assert len(client.calls) == 1
    assert "response_format" in client.calls[0]


@pytest.mark.unit
def test_request_provider_completion_routes_anthropic():
    client = FakeAnthropicClient('{"signals":[]}')
    result = request_provider_completion("anthropic", client, parser_provider_config(), "hello")
    assert result == '{"signals":[]}'
    assert len(client.calls) == 1
    assert client.calls[0]["model"] == "claude-sonnet-4-5"


@pytest.mark.unit
def test_request_provider_completion_routes_google():
    client = FakeGoogleClient('{"signals":[]}')
    result = request_provider_completion("google", client, parser_provider_config(), "hello")
    assert result == '{"signals":[]}'
    assert client.calls == ["hello"]


@pytest.mark.unit
def test_request_provider_completion_rejects_unknown_provider():
    with pytest.raises(UnsupportedProviderError):
        request_provider_completion("invalid", object(), parser_provider_config(), "hello")
