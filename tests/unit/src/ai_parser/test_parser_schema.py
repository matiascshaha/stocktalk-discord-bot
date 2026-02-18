import pytest

from src.ai_parser import AIParser
from src.models.parser_models import ParsedMessage
from tests.testkit.datasets.stocktalk_real_messages import REAL_MESSAGES
from tests.testkit.doubles.ai_clients import CapturingOpenAIClient, ErrorOpenAIClient, FakeOpenAIClient


@pytest.mark.contract
@pytest.mark.unit
def test_parser_output_has_required_signal_fields_for_runtime():
    parser = AIParser()
    parser.provider = "openai"
    parser.client = FakeOpenAIClient(
        """
        {
          "signals": [
            {
              "ticker": "$aapl",
              "action": "buy",
              "confidence": "0.91",
              "vehicles": [{"type": "stock", "intent": "execute"}]
            }
          ]
        }
        """
    )

    result = parser.parse("Adding AAPL", "tester")
    parsed = ParsedMessage.model_validate(result)
    assert parsed.contract_version == "1.0"
    assert len(parsed.signals) == 1

    signal = parsed.signals[0]
    dumped_signal = result["signals"][0]

    for field in (
        "ticker",
        "action",
        "confidence",
        "weight_percent",
        "urgency",
        "sentiment",
        "reasoning",
        "is_actionable",
        "vehicles",
    ):
        assert field in dumped_signal

    assert signal.ticker == "AAPL"
    assert signal.action == "BUY"
    assert 0.0 <= signal.confidence <= 1.0
    assert len(signal.vehicles) == 1
    assert signal.vehicles[0].type == "STOCK"
    assert signal.vehicles[0].intent == "EXECUTE"


@pytest.mark.contract
@pytest.mark.unit
def test_parser_drops_invalid_signal_entries():
    parser = AIParser()
    parser.provider = "openai"
    parser.client = FakeOpenAIClient(
        """
        {
          "signals": [
            {"action": "BUY", "confidence": 0.8},
            {
              "ticker": "MSFT",
              "action": "BUY",
              "confidence": 0.9,
              "vehicles": [{"type": "STOCK", "intent": "EXECUTE", "side": "BUY"}]
            }
          ]
        }
        """
    )

    result = parser.parse("Adding MSFT", "tester")
    parsed = ParsedMessage.model_validate(result)
    assert len(parsed.signals) == 1
    assert result["signals"][0]["ticker"] == "MSFT"


@pytest.mark.contract
@pytest.mark.unit
def test_parser_normalizes_invalid_action_to_none():
    parser = AIParser()
    parser.provider = "openai"
    parser.client = FakeOpenAIClient(
        """
        {
          "signals": [
            {
              "ticker": "TSLA",
              "action": "ADD",
              "confidence": 0.8,
              "vehicles": [{"type": "STOCK"}]
            }
          ]
        }
        """
    )

    result = parser.parse("Adding TSLA", "tester")
    parsed = ParsedMessage.model_validate(result)
    assert parsed.signals[0].action == "NONE"


@pytest.mark.contract
@pytest.mark.unit
def test_parser_disables_option_vehicle_when_options_flag_off():
    parser = AIParser()
    parser.provider = "openai"
    parser.client = FakeOpenAIClient(
        """
        {
          "signals": [
            {
              "ticker": "NVDA",
              "action": "BUY",
              "confidence": 0.82,
              "vehicles": [
                {
                  "type": "OPTION",
                  "intent": "EXECUTE",
                  "side": "BUY",
                  "option_type": "CALL",
                  "strike": 140
                }
              ]
            }
          ]
        }
        """
    )

    parser.options_enabled = False
    result = parser.parse("considering NVDA 140c", "tester")
    parsed = ParsedMessage.model_validate(result)

    option_vehicle = parsed.signals[0].vehicles[0]
    assert option_vehicle.type == "OPTION"
    assert option_vehicle.enabled is False


@pytest.mark.contract
@pytest.mark.unit
def test_openai_request_uses_structured_output_response_format():
    parser = AIParser()
    parser.provider = "openai"
    parser.client = CapturingOpenAIClient(
        """
        {
          "signals": [
            {
              "ticker": "AAPL",
              "action": "BUY",
              "confidence": 0.95,
              "vehicles": [{"type": "STOCK", "intent": "EXECUTE", "side": "BUY"}]
            }
          ]
        }
        """
    )

    result = parser.parse("Adding AAPL", "tester")
    assert result["meta"]["status"] == "ok"
    assert len(parser.client.calls) == 1

    call = parser.client.calls[0]
    assert "response_format" in call
    response_format = call["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    schema = response_format["json_schema"]["schema"]
    for key in ("contract_version", "source", "signals", "meta"):
        assert key in schema["required"]


@pytest.mark.contract
@pytest.mark.unit
def test_openai_request_failure_returns_provider_error():
    parser = AIParser()
    parser.provider = "openai"
    parser.client = ErrorOpenAIClient()

    result = parser.parse("Adding MSFT", "tester")
    assert result["meta"]["status"] == "provider_error"
    assert result["signals"] == []
    assert len(parser.client.calls) == 1
    assert "response_format" in parser.client.calls[0]


@pytest.mark.contract
@pytest.mark.unit
def test_portfolio_summary_is_prompt_handled_not_preblocked():
    parser = AIParser()
    parser.provider = "openai"
    parser.client = CapturingOpenAIClient('{"signals": []}')

    portfolio_message = next(
        text
        for _msg_id, _author, text, should_pick, _tickers in REAL_MESSAGES
        if not should_pick and "PORTFOLIO UPDATE" in text
    )

    result = parser.parse(portfolio_message, "stocktalkweekly")
    assert result["meta"]["status"] == "no_action"
    assert result["signals"] == []
    assert len(parser.client.calls) == 1

    prompt = parser.client.calls[0]["messages"][0]["content"]
    assert "If the message is PORTFOLIO_SUMMARY, return no picks." in prompt
    assert "Do NOT treat holdings inventory lines as execution signals" in prompt
