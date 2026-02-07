from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from config.settings import CHANNEL_ID
from src.discord_client import StockMonitorClient


def _message(content: str, author_id: int, channel_id: int):
    author = SimpleNamespace(id=author_id, name=f"user-{author_id}")
    channel = SimpleNamespace(id=channel_id)
    return SimpleNamespace(
        content=content,
        author=author,
        channel=channel,
        jump_url="https://discord.com/mock/message",
    )


@pytest.mark.unit
@pytest.mark.contract
def test_client_initializes():
    client = StockMonitorClient(trader=None)
    assert client.client is not None


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_ignores_wrong_channel():
    client = StockMonitorClient(trader=None)
    type(client.client).user = SimpleNamespace(id=999)
    client.parser.parse = MagicMock(return_value={"picks": [], "meta": {"status": "ok"}})

    await client.on_message(_message("Buy AAPL", author_id=123, channel_id=CHANNEL_ID + 1))
    client.parser.parse.assert_not_called()


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_ignores_own_message():
    client = StockMonitorClient(trader=None)
    type(client.client).user = SimpleNamespace(id=123)
    client.parser.parse = MagicMock(return_value={"picks": [], "meta": {"status": "ok"}})

    await client.on_message(_message("Buy AAPL", author_id=123, channel_id=CHANNEL_ID))
    client.parser.parse.assert_not_called()


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_malformed_parser_response_does_not_notify_or_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.parser.parse = MagicMock(return_value=["bad-shape"])
    client.notifier.notify = MagicMock()

    await client.on_message(_message("Buy AAPL", author_id=321, channel_id=CHANNEL_ID))
    client.notifier.notify.assert_not_called()
    trader.place_stock_order.assert_not_called()


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_valid_pick_triggers_notify_and_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "picks": [
                {
                    "ticker": "AAPL",
                    "action": "BUY",
                    "confidence": 0.9,
                    "weight_percent": 5.0,
                    "urgency": "MEDIUM",
                    "sentiment": "BULLISH",
                    "reasoning": "test",
                }
            ],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(_message("Buy AAPL", author_id=321, channel_id=CHANNEL_ID))
    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_called_once()
