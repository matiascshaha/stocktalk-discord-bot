import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.discord_client as discord_client_module
import src.trading.orders.planner as order_planner_module
from src.discord_client import StockMonitorClient
from tests.testkit.builders.discord_messages import TEST_CHANNEL_ID, build_message
from tests.testkit.builders.parser import parser_with_fake_openai_response
from tests.testkit.doubles.trader_probe import TraderProbe
from tests.testkit.payloads.signals import build_signal_payload
from tests.testkit.scenario_catalogs.parser_messages import PARSER_MESSAGE_PARAMS


pytestmark = [pytest.mark.feature, pytest.mark.happy_path]


@pytest.mark.feature_regression
@pytest.mark.asyncio
async def test_valid_signal_triggers_trade_execution():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY")], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.place_stock_order.assert_called_once()
    order = trader.place_stock_order.call_args[0][0]
    assert order.side == "BUY"


@pytest.mark.asyncio
async def test_off_hours_uses_queued_limit_without_retry(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: False)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "queue_when_closed", True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "queue_time_in_force", "GTC")
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)

    trader = MagicMock()
    trader.get_stock_quotes = MagicMock(return_value=[{"asks": [{"price": "100.0"}], "bids": [{"price": "99.9"}]}])
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY", weight_percent=None)], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.place_stock_order.assert_called_once()
    order = trader.place_stock_order.call_args[0][0]
    assert order.order_type == "LIMIT"
    assert order.time_in_force == "GTC"


@pytest.mark.asyncio
async def test_regular_hours_uses_market_order_without_retry(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)

    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY", weight_percent=None)], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.place_stock_order.assert_called_once()
    order = trader.place_stock_order.call_args[0][0]
    assert order.order_type == "MARKET"


@pytest.mark.feature_regression
@pytest.mark.asyncio
@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", PARSER_MESSAGE_PARAMS)
async def test_real_message_pipeline_fake_ai_to_trader(msg_id, author, text, should_pick, tickers):
    _ = msg_id
    trader = TraderProbe()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client._log_signals = MagicMock()

    if should_pick:
        fake_payload = {
            "signals": [build_signal_payload(ticker, "BUY", confidence=0.95, weight_percent=None) for ticker in sorted(tickers)]
        }
    else:
        fake_payload = {"signals": []}
    client.parser = parser_with_fake_openai_response(json.dumps(fake_payload))

    await client.on_message(build_message(text, author_id=321, channel_id=TEST_CHANNEL_ID))

    if should_pick:
        assert len(trader.orders) == len(tickers)
        assert trader.account_requests >= 1
        parsed_payload = client.notifier.notify.call_args[0][0]
        found = {signal["ticker"] for signal in parsed_payload["signals"]}
        for ticker in tickers:
            assert ticker in found
    else:
        assert trader.orders == []
        client.notifier.notify.assert_not_called()
