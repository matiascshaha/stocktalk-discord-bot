import json

import pytest

from src.ai_parser import AIParser
from tests.testkit.scenario_catalogs.parser_messages import PARSER_MESSAGE_PARAMS
from tests.testkit.builders.parser import parser_with_fake_openai_response


pytestmark = [pytest.mark.contract]


def test_parse_no_client_returns_empty_result():
    parser = AIParser()
    parser.client = None
    parser.provider = None

    result = parser.parse("Buying AAPL now", "tester")
    assert isinstance(result, dict)
    assert result["signals"] == []
    assert result["meta"]["status"] == "no_client"


def test_parse_malformed_json_returns_invalid_json_status():
    parser = parser_with_fake_openai_response("not-json")

    result = parser.parse("Buying AAPL now", "tester")
    assert result["signals"] == []
    assert result["meta"]["status"] == "invalid_json"


def test_parse_normalizes_signal_list_response():
    parser = parser_with_fake_openai_response(
        '[{"ticker":"AAPL","action":"BUY","confidence":0.8,"vehicles":[{"type":"STOCK","intent":"EXECUTE","side":"BUY"}]}]'
    )

    result = parser.parse("Buying AAPL now", "tester")
    assert result["meta"]["status"] == "ok"
    assert len(result["signals"]) == 1
    assert result["signals"][0]["ticker"] == "AAPL"


def test_parse_normalizes_single_signal_dict_response():
    parser = parser_with_fake_openai_response(
        '{"ticker":"MSFT","action":"BUY","confidence":0.7,"vehicles":[{"type":"STOCK","intent":"EXECUTE","side":"BUY"}]}'
    )

    result = parser.parse("Buying MSFT now", "tester")
    assert result["meta"]["status"] == "ok"
    assert len(result["signals"]) == 1
    assert result["signals"][0]["ticker"] == "MSFT"


@pytest.mark.feature_regression
@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", PARSER_MESSAGE_PARAMS)
def test_regression_real_messages_with_fixed_ai_contract(msg_id, author, text, should_pick, tickers):
    _ = msg_id

    if should_pick:
        fake_payload = {
            "signals": [
                {
                    "ticker": ticker,
                    "action": "BUY",
                    "confidence": 0.9,
                    "vehicles": [{"type": "STOCK", "intent": "EXECUTE", "side": "BUY"}],
                }
                for ticker in sorted(tickers)
            ]
        }
    else:
        fake_payload = {"signals": []}

    parser = parser_with_fake_openai_response(json.dumps(fake_payload))
    result = parser.parse(text, author)

    assert isinstance(result, dict)
    assert "signals" in result
    assert isinstance(result["signals"], list)

    found = {signal["ticker"] for signal in result["signals"] if isinstance(signal, dict) and signal.get("ticker")}
    if should_pick:
        for ticker in tickers:
            assert ticker in found, f"{msg_id} missing ticker {ticker}"
    else:
        assert found == set(), f"{msg_id} should not produce signals"
