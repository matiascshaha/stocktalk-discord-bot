from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.discord_client import StockMonitorClient
from tests.testkit.builders.discord_messages import TEST_CHANNEL_ID, WRONG_CHANNEL_ID, build_message


pytestmark = [pytest.mark.feature, pytest.mark.edge_case]


@pytest.mark.asyncio
async def test_ignores_wrong_channel():
    client = StockMonitorClient(trader=None)
    type(client.client).user = SimpleNamespace(id=999)
    client.parser.parse = MagicMock(return_value={"signals": [], "meta": {"status": "ok"}})

    await client.on_message(build_message("Buy AAPL", author_id=123, channel_id=WRONG_CHANNEL_ID))
    client.parser.parse.assert_not_called()


@pytest.mark.asyncio
async def test_ignores_own_message():
    client = StockMonitorClient(trader=None)
    type(client.client).user = SimpleNamespace(id=123)
    client.parser.parse = MagicMock(return_value={"signals": [], "meta": {"status": "ok"}})

    await client.on_message(build_message("Buy AAPL", author_id=123, channel_id=TEST_CHANNEL_ID))
    client.parser.parse.assert_not_called()


@pytest.mark.asyncio
async def test_malformed_parser_response_does_not_notify_or_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.parser.parse = MagicMock(return_value=["bad-shape"])
    client.notifier.notify = MagicMock()

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    client.notifier.notify.assert_not_called()
    trader.place_stock_order.assert_not_called()
