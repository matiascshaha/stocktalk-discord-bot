import pytest

from src.brokerages.webull.mapper import _enum_value, _extract_order_id, to_order_result, to_webull_stock_order
from src.trading.contracts import OrderType, StockOrder, TradingSession


pytestmark = [pytest.mark.unit]


def test_to_webull_stock_order_maps_core_fields():
    order = StockOrder(
        symbol="aapl",
        side="BUY",
        quantity=2,
        order_type=OrderType.LIMIT,
        limit_price=101.25,
        trading_session=TradingSession.ALL,
        extended_hours_trading=True,
    )

    mapped = to_webull_stock_order(order)

    assert mapped.symbol == "AAPL"
    assert mapped.side == "BUY"
    assert mapped.order_type == "LIMIT"
    assert mapped.limit_price == 101.25
    assert mapped.trading_session == "ALL"
    assert mapped.extended_hours_trading is True


def test_to_webull_stock_order_omits_limit_price_for_market_order():
    order = StockOrder(symbol="MSFT", side="SELL", quantity=1, order_type=OrderType.MARKET)

    mapped = to_webull_stock_order(order)

    assert mapped.order_type == "MARKET"
    assert mapped.limit_price is None


def test_to_order_result_wraps_non_dict_payload():
    result = to_order_result("ok")

    assert result.success is True
    assert result.raw == {"response": "ok"}
    assert result.order_id is None


def test_to_order_result_extracts_nested_order_id():
    result = to_order_result({"data": [{"orderId": 12345}]})

    assert result.order_id == "12345"


def test_extract_order_id_handles_multiple_shapes():
    assert _extract_order_id({"order_id": "a"}) == "a"
    assert _extract_order_id({"orderId": "b"}) == "b"
    assert _extract_order_id({"id": "c"}) == "c"
    assert _extract_order_id({"data": {"order_id": 99}}) == "99"
    assert _extract_order_id({"data": [{"order_id": "d"}]}) == "d"
    assert _extract_order_id({"data": []}) is None


def test_enum_value_normalizes_enums_strings_and_none():
    assert _enum_value(OrderType.MARKET) == "MARKET"
    assert _enum_value(" buy ") == "BUY"
    assert _enum_value(None) == ""
