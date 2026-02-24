import pytest

from src.utils.validators import validate_confidence, validate_pick, validate_ticker, validate_weight


pytestmark = [pytest.mark.unit]


def test_validate_ticker_accepts_valid_uppercase_symbol():
    assert validate_ticker("AAPL") is True


def test_validate_ticker_rejects_invalid_values():
    assert validate_ticker("") is False
    assert validate_ticker("aa") is False
    assert validate_ticker("AAPL1") is False
    assert validate_ticker("TOOLONG") is False


def test_validate_confidence_accepts_range_and_rejects_invalid():
    assert validate_confidence(0.0) is True
    assert validate_confidence(1.0) is True
    assert validate_confidence("0.5") is True
    assert validate_confidence(1.1) is False
    assert validate_confidence("bad") is False


def test_validate_weight_optional_and_range_rules():
    assert validate_weight(None) is True
    assert validate_weight(50) is True
    assert validate_weight("100") is True
    assert validate_weight(0) is False
    assert validate_weight(120) is False


def test_validate_pick_accepts_valid_payload():
    ok, error = validate_pick(
        {
            "ticker": "MSFT",
            "action": "BUY",
            "confidence": 0.9,
            "option_type": "STOCK",
            "urgency": "MEDIUM",
            "sentiment": "BULLISH",
            "reasoning": "breakout",
            "weight": 10,
        }
    )
    assert ok is True
    assert error is None


def test_validate_pick_rejects_missing_field():
    ok, error = validate_pick(
        {
            "ticker": "MSFT",
            "action": "BUY",
            "confidence": 0.9,
            "option_type": "STOCK",
            "urgency": "MEDIUM",
            "sentiment": "BULLISH",
        }
    )
    assert ok is False
    assert "Missing required field" in error


def test_validate_pick_rejects_invalid_action():
    ok, error = validate_pick(
        {
            "ticker": "MSFT",
            "action": "ADD",
            "confidence": 0.9,
            "option_type": "STOCK",
            "urgency": "MEDIUM",
            "sentiment": "BULLISH",
            "reasoning": "x",
        }
    )
    assert ok is False
    assert "Invalid action" in error
