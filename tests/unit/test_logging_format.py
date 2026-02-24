import pytest

from src.utils.logging_format import _flag, format_mode_summary, format_pick_summary, format_startup_status


pytestmark = [pytest.mark.unit]


def test_flag_formats_truthy_and_falsy_values():
    assert _flag(True) == "ON"
    assert _flag(0) == "OFF"


def test_format_mode_summary_includes_key_fields():
    summary = format_mode_summary(
        {
            "broker": "WEBULL",
            "auto_trade": True,
            "paper_trade": False,
            "options_enabled": True,
            "min_confidence": 0.7,
            "default_amount": 1000,
            "use_market_orders": True,
        }
    )

    assert "broker=webull" in summary
    assert "auto_trade=ON" in summary
    assert "paper_trade=OFF" in summary
    assert "min_confidence=0.70" in summary


def test_format_startup_status_builds_readable_lines():
    lines = format_startup_status("user#1", 123, "openai", True, False, "1.0")

    assert len(lines) == 7
    assert "Logged in as: user#1" in lines[1]
    assert "AI parser: Openai" in lines[3]
    assert "Auto-trading: ENABLED" in lines[5]
    assert "Options execution: DISABLED" in lines[6]


def test_format_pick_summary_handles_signals_and_empty_payload():
    assert format_pick_summary({"signals": []}) == "No actionable signals detected."

    summary = format_pick_summary(
        {
            "signals": [
                {"ticker": "AAPL", "action": "BUY"},
                {"ticker": "TSLA", "action": "SELL"},
            ]
        }
    )

    assert "count=2" in summary
    assert "tickers=AAPL, TSLA" in summary
    assert "actions=BUY, SELL" in summary
