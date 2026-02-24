from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.providers.anthropic.parser_client import request_parser_completion as request_anthropic_parser_completion
from src.providers.google.parser_client import request_parser_completion as request_google_parser_completion
from src.providers.openai.parser_client import (
    extract_structured_message_content,
    request_parser_completion as request_openai_parser_completion,
)
from src.providers.openai.parser_contract import parser_response_format


pytestmark = [pytest.mark.unit]


def test_extract_structured_message_content_from_plain_string():
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=' {"signals": []} '))]
    )

    assert extract_structured_message_content(response) == '{"signals": []}'


def test_extract_structured_message_content_from_content_list_of_dicts():
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content=[{"text": "{"}, {"text": '"signals": []}'}]))
        ]
    )

    assert extract_structured_message_content(response) == '{"signals": []}'


def test_extract_structured_message_content_from_content_list_objects():
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content=[SimpleNamespace(text="{"), SimpleNamespace(text='"ok":1}')]))
        ]
    )

    assert extract_structured_message_content(response) == '{"ok":1}'


def test_extract_structured_message_content_from_parsed_model_dump():
    parsed = MagicMock()
    parsed.model_dump.return_value = {"signals": []}
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=[], parsed=parsed))])

    assert extract_structured_message_content(response) == '{"signals": []}'


def test_extract_structured_message_content_raises_when_no_content():
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=[]))])

    with pytest.raises(ValueError, match="no parseable"):
        extract_structured_message_content(response)


def test_openai_request_parser_completion_passes_response_format(monkeypatch):
    create = MagicMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"signals": []}'))]
        )
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    result = request_openai_parser_completion(
        client=client,
        model="gpt-test",
        prompt="hello",
        max_tokens=123,
        temperature=0.1,
    )

    assert result == '{"signals": []}'
    kwargs = create.call_args.kwargs
    assert kwargs["model"] == "gpt-test"
    assert kwargs["max_tokens"] == 123
    assert kwargs["temperature"] == 0.1
    assert kwargs["response_format"]["type"] == "json_schema"


def test_anthropic_request_parser_completion_strips_text():
    create = MagicMock(return_value=SimpleNamespace(content=[SimpleNamespace(text=' {"signals": []} ')]))
    client = SimpleNamespace(messages=SimpleNamespace(create=create))

    result = request_anthropic_parser_completion(
        client=client,
        model="claude",
        prompt="hello",
        max_tokens=200,
        temperature=0.2,
    )

    assert result == '{"signals": []}'
    assert create.call_args.kwargs["model"] == "claude"


def test_google_request_parser_completion_strips_text():
    generate = MagicMock(return_value=SimpleNamespace(text=' {"signals": []} '))
    client = SimpleNamespace(generate_content=generate)

    result = request_google_parser_completion(client=client, prompt="hello")

    assert result == '{"signals": []}'
    generate.assert_called_once_with("hello")


def test_parser_response_format_is_strict_json_schema():
    response_format = parser_response_format()

    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["name"] == "stocktalk_parser_contract"
    assert "signals" in response_format["json_schema"]["schema"]["required"]
