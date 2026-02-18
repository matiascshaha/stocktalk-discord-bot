import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.discord_client as discord_client_module
import src.trading.orders.planner as order_planner_module
from src.discord_client import StockMonitorClient
from tests.support.cases.parser_messages import PARSER_MESSAGE_PARAMS
from tests.support.factories.discord_messages import TEST_CHANNEL_ID, WRONG_CHANNEL_ID, build_message
from tests.support.factories.parser import parser_with_fake_openai_response
from tests.support.fakes.trader_probe import TraderProbe
from tests.support.payloads.signals import build_signal_payload


PIPELINE_CASES = PARSER_MESSAGE_PARAMS


@pytest.mark.integration
def test_client_initializes():
    client = StockMonitorClient(trader=None)
    assert client.client is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ignores_wrong_channel():
    client = StockMonitorClient(trader=None)
    type(client.client).user = SimpleNamespace(id=999)
    client.parser.parse = MagicMock(return_value={"signals": [], "meta": {"status": "ok"}})

    await client.on_message(build_message("Buy AAPL", author_id=123, channel_id=WRONG_CHANNEL_ID))
    client.parser.parse.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ignores_own_message():
    client = StockMonitorClient(trader=None)
    type(client.client).user = SimpleNamespace(id=123)
    client.parser.parse = MagicMock(return_value={"signals": [], "meta": {"status": "ok"}})

    await client.on_message(build_message("Buy AAPL", author_id=123, channel_id=TEST_CHANNEL_ID))
    client.parser.parse.assert_not_called()


@pytest.mark.integration
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


@pytest.mark.integration
@pytest.mark.feature_regression
@pytest.mark.asyncio
async def test_valid_signal_triggers_notify_and_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY")], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_called_once()
    order = trader.place_stock_order.call_args[0][0]
    assert order.side == "BUY"


@pytest.mark.integration
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


@pytest.mark.integration
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


@pytest.mark.integration
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


@pytest.mark.integration
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


@pytest.mark.integration
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


@pytest.mark.integration
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_trade_failure_does_not_crash_message_handler():
    trader = MagicMock()
    trader.place_stock_order = MagicMock(side_effect=RuntimeError("INVALID_PARAMETER"))

    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY")], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_called_once()


@pytest.mark.integration
@pytest.mark.feature_regression
@pytest.mark.asyncio
@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", PIPELINE_CASES)
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
