from types import SimpleNamespace

import pytest

from src.ai_parser import AIParser


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
def test_parser_output_has_required_fields_for_discord_client():
    parser = AIParser()
    parser.provider = "openai"
    parser.client = _FakeOpenAIClient(
        """
        {
          "picks": [
            {"ticker": "$aapl", "action": "buy", "confidence": "0.91"}
          ]
        }
        """
    )

    result = parser.parse("Adding AAPL", "tester")
    assert len(result["picks"]) == 1
    pick = result["picks"][0]

    for field in ("ticker", "action", "confidence", "weight_percent", "urgency", "sentiment", "reasoning"):
        assert field in pick

    assert pick["ticker"] == "AAPL"
    assert pick["action"] == "BUY"
    assert 0.0 <= pick["confidence"] <= 1.0


@pytest.mark.contract
@pytest.mark.unit
def test_parser_drops_invalid_pick_entries():
    parser = AIParser()
    parser.provider = "openai"
    parser.client = _FakeOpenAIClient(
        """
        {
          "picks": [
            {"action": "BUY", "confidence": 0.8},
            {"ticker": "MSFT", "action": "BUY", "confidence": 0.9}
          ]
        }
        """
    )

    result = parser.parse("Adding MSFT", "tester")
    assert len(result["picks"]) == 1
    assert result["picks"][0]["ticker"] == "MSFT"
