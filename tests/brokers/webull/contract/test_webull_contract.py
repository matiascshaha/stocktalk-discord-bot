from unittest.mock import MagicMock

import pytest

from src.models.webull_models import OptionLeg, OptionOrderRequest, OptionType, OrderSide, OrderType, StockOrderRequest


pytestmark = [pytest.mark.contract, pytest.mark.broker, pytest.mark.broker_webull]


def test_sdk_method_compatibility(trader):
    v1_methods = {method for method in dir(trader.order_api) if not method.startswith("_")}
    v2_methods = {method for method in dir(trader.order_v2_api) if not method.startswith("_")}

    assert "place_order" in v1_methods
    assert "preview_option" in v2_methods
    assert "place_option" in v2_methods


def test_build_stock_payload(trader):
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 200.0}])
    order = StockOrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        order_type=OrderType.LIMIT,
        limit_price=190.0,
    )

    payload = trader._build_stock_payload(order)
    assert payload["instrument_id"] == "AAPL_ID"
    assert payload["qty"] == 2
    assert payload["side"] == "BUY"
    assert payload["order_type"] == "LIMIT"
    assert payload["limit_price"] == "190.0"


def test_build_stock_payload_normalizes_fractional_quantity_to_whole_share(trader):
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 200.0}])
    order = StockOrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2.9,
        order_type=OrderType.MARKET,
    )

    payload = trader._build_stock_payload(order)
    assert payload["qty"] == 2


def test_build_stock_payload_rejects_sub_share_quantity(trader):
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 200.0}])
    order = StockOrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=0.2,
        order_type=OrderType.MARKET,
    )

    with pytest.raises(ValueError):
        trader._build_stock_payload(order)


def test_option_order_model_dump_contains_expected_fields(trader):
    order = OptionOrderRequest(
        order_type=OrderType.LIMIT,
        quantity="1",
        limit_price="2.50",
        side=OrderSide.BUY,
        legs=[
            OptionLeg(
                side=OrderSide.BUY,
                quantity="1",
                symbol="TSLA",
                strike_price="400",
                option_expire_date="2025-11-26",
                option_type=OptionType.CALL,
                market="US",
            )
        ],
    )

    payload = order.model_dump(exclude_none=True)
    assert payload["order_type"] == "LIMIT"
    assert payload["quantity"] == "1"
    assert payload["limit_price"] == "2.50"
    assert payload["legs"][0]["instrument_type"] == "OPTION"
    assert payload["legs"][0]["market"] == "US"


def test_preview_stock_order_local_estimate(trader):
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 150.0}])
    order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=2, order_type=OrderType.MARKET)

    preview = trader.preview_stock_order(order)
    assert preview.estimated_cost == "300.00"
    assert preview.currency is not None


def test_get_instrument_raises_on_bad_response(trader):
    response = MagicMock(status_code=500, text="bad response")
    trader.instrument_api.get_instrument = MagicMock(return_value=response)

    with pytest.raises(RuntimeError):
        trader.get_instrument("AAPL")
