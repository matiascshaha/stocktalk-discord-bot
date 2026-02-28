from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.discord_client as discord_client_module
import src.trading.orders.planner as order_planner_module
import src.webull_trader as webull_trader_module
from src.brokerages.webull.broker import WebullBroker
from src.discord_client import StockMonitorClient
from src.models.webull_models import AccountBalanceResponse, AccountCurrencyAsset
from src.webull_trader import WebullTrader
from tests.data.stocktalk_real_messages import MESSAGE_FIXTURES
from tests.support.factories.discord_messages import TEST_CHANNEL_ID, build_message
from tests.support.payloads.signals import build_signal_payload


pytestmark = [
    pytest.mark.integration,
    pytest.mark.broker,
    pytest.mark.broker_webull,
    pytest.mark.channel,
    pytest.mark.source_discord,
]

FROZEN_COMMON_SHARES_MESSAGE = MESSAGE_FIXTURES["frozen_common_shares"].text
FROZEN_WEIGHTED_MESSAGE = MESSAGE_FIXTURES["frozen_weighted"].text
FROZEN_DOLLAR_AMOUNT_MESSAGE = MESSAGE_FIXTURES["frozen_dollar_amount"].text


@pytest.mark.asyncio
async def test_weighted_order_skips_submit_when_buying_power_is_unavailable(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "force_default_amount_for_buys", False)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "fallback_to_default_amount_on_weighting_failure", False)

    response_payload = {"order_id": "unused-order", "status": "accepted"}
    fake_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: response_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_response))
    trader.resolve_account_id = MagicMock(return_value="paper-account-1")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 100.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=5000.0, cash_power=0.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=None)
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    trader._enforce_margin_buffer = MagicMock()

    broker = WebullBroker(trader)
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "signals": [build_signal_payload("AAPL", "BUY", confidence=0.95, weight_percent=12.5)],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(build_message(FROZEN_WEIGHTED_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID))

    trader._get_buying_power.assert_called_once()
    trader.order_api.place_order.assert_not_called()
    assert isolated_picks_log_path.exists()


@pytest.mark.asyncio
async def test_order_skips_submit_when_margin_buffer_is_violated(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "force_default_amount_for_buys", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "default_amount", 1000.0)

    response_payload = {"order_id": "unused-order", "status": "accepted"}
    fake_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: response_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_response))
    trader.resolve_account_id = MagicMock(return_value="paper-account-2")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 100.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=5000.0, cash_power=2500.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=2500.0)
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    trader._enforce_margin_buffer = MagicMock(side_effect=ValueError("Margin buffer violated"))

    broker = WebullBroker(trader)
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "signals": [build_signal_payload("AAPL", "BUY", confidence=0.95, weight_percent=None)],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(
        build_message(FROZEN_COMMON_SHARES_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID)
    )

    trader._enforce_margin_buffer.assert_called_once()
    trader.order_api.place_order.assert_not_called()
    assert isolated_picks_log_path.exists()


@pytest.mark.asyncio
async def test_order_skips_submit_when_default_notional_cannot_buy_one_share(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "force_default_amount_for_buys", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "default_amount", 5.0)

    response_payload = {"order_id": "unused-order", "status": "accepted"}
    fake_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: response_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_response))
    trader.resolve_account_id = MagicMock(return_value="paper-account-3")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "BRKA_ID", "last_price": 1000.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=100.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=100.0)
    trader.get_current_stock_quote = MagicMock(return_value=1000.0)
    trader._enforce_margin_buffer = MagicMock()

    broker = WebullBroker(trader)
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "signals": [build_signal_payload("BRKA", "BUY", confidence=0.88, weight_percent=None)],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(
        build_message(FROZEN_DOLLAR_AMOUNT_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID)
    )

    trader.order_api.place_order.assert_not_called()
    assert isolated_picks_log_path.exists()


@pytest.mark.asyncio
async def test_order_submit_rejection_is_caught_and_handler_continues(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "force_default_amount_for_buys", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "default_amount", 1000.0)

    fake_response = SimpleNamespace(
        status_code=500,
        text='{"message": "insufficient buying power"}',
        json=lambda: {"message": "insufficient buying power"},
    )

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_response))
    trader.resolve_account_id = MagicMock(return_value="paper-account-4")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 100.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=5000.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=5000.0)
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    trader._enforce_margin_buffer = MagicMock()

    broker = WebullBroker(trader)
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "signals": [build_signal_payload("AAPL", "BUY", confidence=0.9, weight_percent=None)],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(
        build_message(FROZEN_COMMON_SHARES_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID)
    )

    trader.order_api.place_order.assert_called_once()
    assert isolated_picks_log_path.exists()
