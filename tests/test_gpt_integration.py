import json
import os
from types import SimpleNamespace

import pytest

from src.ai_parser import AIParser
from tests.data.stocktalk_real_messages import REAL_MESSAGES


class _FakeOpenAIClient:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        _ = kwargs
        message = SimpleNamespace(content=self._response_text)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _parser_with_fake_response(response_text: str) -> AIParser:
    parser = AIParser()
    parser.provider = "openai"
    parser.client = _FakeOpenAIClient(response_text)
    return parser


@pytest.mark.unit
@pytest.mark.contract
def test_parse_no_client_returns_empty_result():
    parser = AIParser()
    parser.client = None
    parser.provider = None

    result = parser.parse("Buying AAPL now", "tester")
    assert isinstance(result, dict)
    assert result["picks"] == []
    assert result["meta"]["status"] == "no_client"


@pytest.mark.unit
@pytest.mark.contract
def test_parse_malformed_json_returns_invalid_json_status():
    parser = _parser_with_fake_response("not-json")

    result = parser.parse("Buying AAPL now", "tester")
    assert result["picks"] == []
    assert result["meta"]["status"] == "invalid_json"


@pytest.mark.unit
@pytest.mark.contract
def test_parse_normalizes_list_response():
    parser = _parser_with_fake_response('[{"ticker":"AAPL","action":"BUY","confidence":0.8}]')

    result = parser.parse("Buying AAPL now", "tester")
    assert result["meta"]["status"] == "ok"
    assert len(result["picks"]) == 1
    assert result["picks"][0]["ticker"] == "AAPL"


@pytest.mark.unit
@pytest.mark.contract
def test_parse_normalizes_single_pick_dict_response():
    parser = _parser_with_fake_response('{"ticker":"MSFT","action":"BUY","confidence":0.7}')

    result = parser.parse("Buying MSFT now", "tester")
    assert result["meta"]["status"] == "ok"
    assert len(result["picks"]) == 1
    assert result["picks"][0]["ticker"] == "MSFT"


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", REAL_MESSAGES)
def test_regression_real_messages_with_fixed_ai_contract(msg_id, author, text, should_pick, tickers):
    if should_pick:
        fake_payload = {"picks": [{"ticker": t, "action": "BUY", "confidence": 0.9} for t in sorted(tickers)]}
    else:
        fake_payload = {"picks": []}

    parser = _parser_with_fake_response(json.dumps(fake_payload))
    result = parser.parse(text, author)

    assert isinstance(result, dict)
    assert "picks" in result
    assert isinstance(result["picks"], list)

    found = {p["ticker"] for p in result["picks"] if isinstance(p, dict) and p.get("ticker")}
    if should_pick:
        for ticker in tickers:
            assert ticker in found, f"{msg_id} missing ticker {ticker}"
    else:
        assert found == set(), f"{msg_id} should not produce picks"


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", REAL_MESSAGES)
def test_live_ai_smoke(msg_id, author, text, should_pick, tickers):
    if os.getenv("RUN_LIVE_AI_TESTS") != "1":
        pytest.skip("RUN_LIVE_AI_TESTS != 1")

    parser = AIParser()
    result = parser.parse(text, author)
    picks = result.get("picks", [])
    found = {p["ticker"] for p in picks if isinstance(p, dict) and p.get("ticker")}

    if should_pick:
        for ticker in tickers:
            assert ticker in found, f"{msg_id} missing ticker {ticker}"
    else:
        assert found == set(), f"{msg_id} should not produce picks"
