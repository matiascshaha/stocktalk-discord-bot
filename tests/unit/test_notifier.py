from unittest.mock import MagicMock

import pytest

from src.notifier import Notifier


pytestmark = [pytest.mark.unit]


def test_notify_returns_early_for_empty_payload():
    notifier = Notifier()
    notifier._print_console_notification = MagicMock()

    notifier.notify(None, "author")

    notifier._print_console_notification.assert_not_called()


def test_notify_prints_console_for_signal_payload():
    notifier = Notifier()
    notifier._print_console_notification = MagicMock()

    notifier.notify({"signals": [{"ticker": "AAPL"}]}, "author")

    notifier._print_console_notification.assert_called_once()


def test_signal_objs_handles_non_dict_payload():
    notifier = Notifier()
    assert notifier._signal_objs("bad") == []


def test_print_console_notification_includes_signal_details(capsys):
    notifier = Notifier()
    payload = {
        "signals": [
            {
                "ticker": "AAPL",
                "action": "BUY",
                "confidence": 0.9,
                "weight_percent": 3.0,
                "urgency": "MEDIUM",
                "sentiment": "BULLISH",
                "reasoning": "Test signal",
                "vehicles": [{"type": "STOCK"}],
            }
        ]
    }

    notifier._print_console_notification(payload, "stocktalkweekly")
    captured = capsys.readouterr()

    assert "STOCK SIGNAL DETECTED from stocktalkweekly" in captured.out
    assert "Ticker: AAPL" in captured.out
    assert "Action: BUY" in captured.out
    assert "Confidence: 90.0%" in captured.out
    assert "Vehicles: STOCK" in captured.out
