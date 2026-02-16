from types import SimpleNamespace

import pytest

from src.ai_parser import AIParser
from src.models.parser_models import ParsedMessage


class _FakeOpenAIClient:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        _ = kwargs
        message = SimpleNamespace(content=self._response_text)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.mark.contract
@pytest.mark.unit
def test_parser_output_has_required_signal_fields_for_runtime():
    parser = AIParser()
    parser.provider = "openai"
    parser.client = _FakeOpenAIClient(
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
    parser.client = _FakeOpenAIClient(
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
    parser.client = _FakeOpenAIClient(
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
def test_parser_disables_option_vehicle_when_options_flag_off(monkeypatch):
    parser = AIParser()
    parser.provider = "openai"
    parser.client = _FakeOpenAIClient(
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
