import os

import pytest

from src.providers.parser_dispatch import UnsupportedProviderError, request_provider_completion
from tests.support.fakes.ai_clients import CapturingOpenAIClient, FakeAnthropicClient, FakeGoogleClient
from tests.support.provider_configs import parser_provider_config

RUN_OPTIONAL_PROVIDER_TESTS = os.getenv("RUN_OPTIONAL_PROVIDER_TESTS") == "1"
OPTIONAL_PROVIDER_TESTS_REASON = "Optional provider tests are disabled. Set RUN_OPTIONAL_PROVIDER_TESTS=1 to run."


@pytest.mark.unit
def test_request_provider_completion_routes_openai():
    client = CapturingOpenAIClient('{"signals":[]}')
    result = request_provider_completion("openai", client, parser_provider_config(), "hello")
    assert result == '{"signals":[]}'
    assert len(client.calls) == 1
    assert "response_format" in client.calls[0]


@pytest.mark.unit
def test_request_provider_completion_routes_openai_with_overrides():
    client = CapturingOpenAIClient('{"signals":[]}')
    result = request_provider_completion(
        "openai",
        client,
        parser_provider_config(),
        "hello",
        model_override="gpt-4.1-mini",
        max_tokens_override=1800,
        temperature_override=0.0,
    )
    assert result == '{"signals":[]}'
    call = client.calls[0]
    assert call["model"] == "gpt-4.1-mini"
    assert call["max_tokens"] == 1800
    assert call["temperature"] == 0.0


@pytest.mark.unit
@pytest.mark.skipif(not RUN_OPTIONAL_PROVIDER_TESTS, reason=OPTIONAL_PROVIDER_TESTS_REASON)
def test_request_provider_completion_routes_anthropic():
    client = FakeAnthropicClient('{"signals":[]}')
    result = request_provider_completion("anthropic", client, parser_provider_config(), "hello")
    assert result == '{"signals":[]}'
    assert len(client.calls) == 1
    assert client.calls[0]["model"] == "claude-sonnet-4-5"


@pytest.mark.unit
@pytest.mark.skipif(not RUN_OPTIONAL_PROVIDER_TESTS, reason=OPTIONAL_PROVIDER_TESTS_REASON)
def test_request_provider_completion_routes_google():
    client = FakeGoogleClient('{"signals":[]}')
    result = request_provider_completion("google", client, parser_provider_config(), "hello")
    assert result == '{"signals":[]}'
    assert client.calls == ["hello"]


@pytest.mark.unit
def test_request_provider_completion_rejects_unknown_provider():
    with pytest.raises(UnsupportedProviderError):
        request_provider_completion("invalid", object(), parser_provider_config(), "hello")
