import pytest

from src.brokerages.webull.stock_payload_builder import (
    WebullStockPayloadBuilder,
    normalize_stock_quantity,
    resolve_notional_sizing_price,
)
from src.models.webull_models import AccountBalanceResponse, AccountCurrencyAsset, OrderSide, OrderType, StockOrderRequest


pytestmark = [pytest.mark.unit]


def test_builder_notional_path_does_not_mutate_input_order_quantity():
    order = StockOrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        order_type=OrderType.LIMIT,
        limit_price=100.0,
    )
    balance = AccountBalanceResponse(account_currency_assets=[AccountCurrencyAsset(cash_power=5000.0)])
    calls = []
    builder = WebullStockPayloadBuilder(
        client_order_id_factory=lambda: "cid-1",
        get_instrument=lambda _: [{"instrument_id": "AAPL_ID", "last_price": 200.0}],
        get_account_balance_contract=lambda: balance,
        get_buying_power=lambda **_: 5000.0,
        get_current_stock_quote=lambda _: 100.0,
        enforce_margin_buffer=lambda payload, estimated_trade_notional: calls.append(
            (payload, estimated_trade_notional)
        ),
    )

    payload = builder.build(order, notional_dollar_amount=1000.0)

    assert payload["qty"] == 10
    assert order.quantity == 1
    assert calls == [(balance, 1000.0)]


def test_builder_weighting_path_does_not_mutate_input_order_quantity():
    order = StockOrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        order_type=OrderType.MARKET,
    )
    balance = AccountBalanceResponse(account_currency_assets=[AccountCurrencyAsset(cash_power=10000.0)])
    calls = []
    builder = WebullStockPayloadBuilder(
        client_order_id_factory=lambda: "cid-2",
        get_instrument=lambda _: [{"instrument_id": "AAPL_ID", "last_price": 200.0}],
        get_account_balance_contract=lambda: balance,
        get_buying_power=lambda **_: 10000.0,
        get_current_stock_quote=lambda _: 50.0,
        enforce_margin_buffer=lambda payload, estimated_trade_notional: calls.append(
            (payload, estimated_trade_notional)
        ),
    )

    payload = builder.build(order, weighting=20.0)

    assert payload["qty"] == 40
    assert order.quantity == 2
    assert calls == [(balance, 2000.0)]


def test_resolve_notional_sizing_price_prefers_snapshot_quote():
    price = resolve_notional_sizing_price(510.0, {"last_price": "500.0"})
    assert price == 510.0


def test_resolve_notional_sizing_price_falls_back_to_instrument_quote():
    price = resolve_notional_sizing_price(None, {"last_price": "500.0"})
    assert price == 500.0


def test_resolve_notional_sizing_price_returns_none_when_no_market_reference_exists():
    price = resolve_notional_sizing_price(None, {"instrument_id": "AAPL_ID"})
    assert price is None


def test_resolve_notional_sizing_price_uses_order_limit_price_as_last_resort():
    price = resolve_notional_sizing_price(
        snapshot_price=None,
        instrument={"instrument_id": "AAPL_ID"},
        order_limit_price=17.44,
    )
    assert price == 17.44


def test_normalize_stock_quantity_rejects_sub_share():
    with pytest.raises(ValueError, match="must be >= 1 share"):
        normalize_stock_quantity(0.5)
