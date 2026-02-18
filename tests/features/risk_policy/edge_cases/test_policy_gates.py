from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.discord_client as discord_client_module
import src.trading.orders.planner as order_planner_module
from src.discord_client import StockMonitorClient
from tests.testkit.builders.discord_messages import TEST_CHANNEL_ID, build_message
from tests.testkit.payloads.signals import build_signal_payload


pytestmark = [pytest.mark.feature, pytest.mark.edge_case]


@pytest.mark.feature_regression
@pytest.mark.asyncio
async def test_missing_weight_uses_default_notional_amount(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "default_amount", 1000.0)

    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY", weight_percent=None)], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.place_stock_order.assert_called_once()
    kwargs = trader.place_stock_order.call_args.kwargs
    assert kwargs["weighting"] is None
    assert kwargs["notional_dollar_amount"] == 1000.0


@pytest.mark.asyncio
async def test_margin_equity_below_threshold_does_not_trade(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)

    trader = MagicMock()
    trader.get_account_balance.return_value = {
        "total_market_value": 10000.0,
        "account_currency_assets": [{"net_liquidation_value": 2000.0, "margin_power": 1000.0, "cash_power": 1000.0}],
    }

    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY", weight_percent=5.0)], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))

    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_not_called()


@pytest.mark.asyncio
async def test_sell_signal_is_blocked_when_no_shorting_rule_enabled():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "SELL")], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Sell AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))

    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_not_called()


@pytest.mark.asyncio
async def test_hold_signal_does_not_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "HOLD")], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Hold AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))

    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_not_called()
