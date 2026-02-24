from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.discord_client as discord_client_module
from src.discord_client import StockMonitorClient
from src.models.parser_models import ParsedSignal


pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_read_channel_history_returns_empty_when_client_not_ready():
    client = StockMonitorClient(trader=None)
    client.client.is_ready = MagicMock(return_value=False)

    messages = await client.read_channel_history(limit=2)

    assert messages == []


@pytest.mark.asyncio
async def test_read_channel_history_returns_empty_when_channel_missing():
    client = StockMonitorClient(trader=None)
    client.client.is_ready = MagicMock(return_value=True)
    client.client.get_channel = MagicMock(return_value=None)

    messages = await client.read_channel_history(limit=2)

    assert messages == []


@pytest.mark.asyncio
async def test_read_channel_history_collects_messages():
    client = StockMonitorClient(trader=None)
    client.client.is_ready = MagicMock(return_value=True)
    message_one = SimpleNamespace(
        author=SimpleNamespace(name="alice"),
        content="first",
        created_at=SimpleNamespace(isoformat=MagicMock(return_value="2026-02-20T10:00:00")),
        id=1,
    )
    message_two = SimpleNamespace(
        author=SimpleNamespace(name="bob"),
        content="second",
        created_at=SimpleNamespace(isoformat=MagicMock(return_value="2026-02-20T10:01:00")),
        id=2,
    )
    history_iter = AsyncMock()
    history_iter.__aiter__.return_value = [message_one, message_two]
    channel = SimpleNamespace(history=MagicMock(return_value=history_iter))
    client.client.get_channel = MagicMock(return_value=channel)

    messages = await client.read_channel_history(limit=2)

    assert len(messages) == 2
    assert messages[0]["author"] == "alice"
    assert messages[1]["message_id"] == 2


def test_signal_to_stock_order_builds_buy_order_for_stock_vehicle():
    client = StockMonitorClient(trader=None)
    signal = ParsedSignal.model_validate(
        {
            "ticker": "AAPL",
            "action": "BUY",
            "confidence": 0.9,
            "reasoning": "x",
            "weight_percent": None,
            "urgency": "MEDIUM",
            "sentiment": "BULLISH",
            "is_actionable": True,
            "vehicles": [{"type": "STOCK", "enabled": True, "intent": "EXECUTE", "side": "BUY"}],
        }
    )

    order = client._signal_to_stock_order(signal)

    assert order is not None
    assert order.symbol == "AAPL"
    assert order.side == "BUY"


def test_signal_to_stock_order_builds_sell_order_for_stock_vehicle():
    client = StockMonitorClient(trader=None)
    signal = ParsedSignal.model_validate(
        {
            "ticker": "AAPL",
            "action": "SELL",
            "confidence": 0.9,
            "reasoning": "x",
            "weight_percent": None,
            "urgency": "MEDIUM",
            "sentiment": "BEARISH",
            "is_actionable": True,
            "vehicles": [{"type": "STOCK", "enabled": True, "intent": "EXECUTE", "side": "SELL"}],
        }
    )

    order = client._signal_to_stock_order(signal)

    assert order is not None
    assert order.side == "SELL"


def test_signal_to_stock_order_returns_none_when_no_executable_stock_vehicle():
    client = StockMonitorClient(trader=None)
    signal = ParsedSignal.model_validate(
        {
            "ticker": "AAPL",
            "action": "BUY",
            "confidence": 0.9,
            "reasoning": "x",
            "weight_percent": None,
            "urgency": "MEDIUM",
            "sentiment": "BULLISH",
            "is_actionable": True,
            "vehicles": [{"type": "OPTION", "enabled": True, "intent": "EXECUTE", "side": "BUY"}],
        }
    )

    order = client._signal_to_stock_order(signal)

    assert order is None


def test_signal_to_stock_order_returns_none_for_non_executable_side_none():
    client = StockMonitorClient(trader=None)
    signal = ParsedSignal.model_validate(
        {
            "ticker": "AAPL",
            "action": "BUY",
            "confidence": 0.9,
            "reasoning": "x",
            "weight_percent": None,
            "urgency": "MEDIUM",
            "sentiment": "BULLISH",
            "is_actionable": True,
            "vehicles": [{"type": "STOCK", "enabled": True, "intent": "EXECUTE", "side": "NONE"}],
        }
    )

    order = client._signal_to_stock_order(signal)

    assert order is None


def test_log_signals_writes_jsonl_entry(tmp_path, monkeypatch):
    client = StockMonitorClient(trader=None)
    log_path = tmp_path / "picks_log.jsonl"
    monkeypatch.setattr(discord_client_module, "PICKS_LOG_PATH", log_path)

    message = SimpleNamespace(
        author="author#1",
        content="Buy AAPL",
        jump_url="https://discord.com/mock/message",
    )
    payload = {"signals": [{"ticker": "AAPL"}], "meta": {"status": "ok"}}

    client._log_signals(message, payload)

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert '"author": "author#1"' in lines[0]
    assert '"ticker": "AAPL"' in lines[0]


def test_run_delegates_to_discord_client_run(monkeypatch):
    client = StockMonitorClient(trader=None)
    client.client.run = MagicMock()
    monkeypatch.setattr(discord_client_module, "DISCORD_TOKEN", "test-token")

    client.run()

    client.client.run.assert_called_once_with("test-token")
