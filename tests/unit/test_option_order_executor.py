from src.trading.orders import OptionOrderExecutor
from src.trading.orders.contracts import OptionLegRequest, OptionOrderRequest, OptionType, OrderSide
from tests.support.fakes.broker_probe import BrokerProbe


def test_option_executor_delegates_to_broker():
    broker = BrokerProbe()
    executor = OptionOrderExecutor(broker)
    order = OptionOrderRequest(
        side=OrderSide.BUY,
        quantity=1,
        legs=[
            OptionLegRequest(
                side=OrderSide.BUY,
                quantity=1,
                symbol="AAPL",
                strike_price=200.0,
                expiry_date="2026-03-20",
                option_type=OptionType.CALL,
            )
        ],
    )

    executor.execute(order)

    assert len(broker.option_orders) == 1
    assert broker.option_orders[0].legs[0].symbol == "AAPL"
