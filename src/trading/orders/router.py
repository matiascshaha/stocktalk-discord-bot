"""Signal-to-order routing for stock and option trade vehicles."""

from typing import Optional

from src.brokerages.base import Brokerage
from src.models.parser_models import ParsedSignal, ParsedVehicle
from src.trading.orders.contracts import (
    BrokerageCapabilityError,
    OptionLegRequest,
    OptionOrderRequest,
    OptionType,
    OrderSide,
    OrderType,
    StockOrderRequest,
    TimeInForce,
)
from src.trading.orders.executor import StockOrderExecutor
from src.trading.orders.option_executor import OptionOrderExecutor
from src.utils.logger import setup_logger


logger = setup_logger("order_router")


class SignalOrderRouter:
    """Route parser vehicles into executable stock/option orders."""

    def __init__(
        self,
        broker: Brokerage,
        stock_executor: StockOrderExecutor,
        option_executor: OptionOrderExecutor,
    ):
        self._broker = broker
        self._stock_executor = stock_executor
        self._option_executor = option_executor

    def execute_signal(self, signal: ParsedSignal) -> None:
        for vehicle in signal.vehicles:
            if not self._is_executable(vehicle):
                continue

            try:
                vehicle_type = str(vehicle.type or "").upper()
                if vehicle_type == "STOCK":
                    self._execute_stock(signal, vehicle)
                    continue
                if vehicle_type == "OPTION":
                    self._execute_option(signal, vehicle)
                    continue

                logger.debug("Skipping unknown vehicle type '%s' for %s", vehicle.type, signal.ticker)
            except Exception as exc:
                logger.error(
                    "Execution failed for %s vehicle on %s: %s",
                    vehicle.type,
                    signal.ticker,
                    exc,
                )

    def _execute_stock(self, signal: ParsedSignal, vehicle: ParsedVehicle) -> None:
        side = self._resolve_side(vehicle)
        if side is None:
            logger.info("Skipping non-executable stock signal for %s", signal.ticker)
            return

        order = StockOrderRequest(symbol=signal.ticker, side=side, quantity=1)
        self._stock_executor.execute(order, weighting=signal.weight_percent)

    def _execute_option(self, signal: ParsedSignal, vehicle: ParsedVehicle) -> None:
        try:
            self._ensure_option_supported()
        except BrokerageCapabilityError as exc:
            logger.error("Skipping option execution for %s: %s", signal.ticker, exc)
            return

        side = self._resolve_side(vehicle)
        if side is None:
            logger.info("Skipping non-executable option signal for %s", signal.ticker)
            return

        if not vehicle.option_type or vehicle.strike is None or not vehicle.expiry:
            logger.warning(
                "Skipping invalid option vehicle for %s (option_type=%s strike=%s expiry=%s)",
                signal.ticker,
                vehicle.option_type,
                vehicle.strike,
                vehicle.expiry,
            )
            return

        quantity = 1
        if vehicle.quantity_hint is not None:
            quantity = max(1, int(float(vehicle.quantity_hint)))

        option_type = OptionType.CALL if str(vehicle.option_type).upper() == "CALL" else OptionType.PUT
        leg = OptionLegRequest(
            side=side,
            quantity=quantity,
            symbol=signal.ticker,
            strike_price=float(vehicle.strike),
            expiry_date=str(vehicle.expiry),
            option_type=option_type,
        )

        order = OptionOrderRequest(
            side=side,
            quantity=quantity,
            legs=[leg],
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )
        self._option_executor.execute(order)

    def _ensure_option_supported(self) -> None:
        capabilities = self._broker.get_capabilities()
        if not capabilities.supports_option_orders:
            raise BrokerageCapabilityError(type(self._broker).__name__, "place_option_order")

    def _is_executable(self, vehicle: ParsedVehicle) -> bool:
        return bool(vehicle.enabled) and str(vehicle.intent).upper() == "EXECUTE"

    def _resolve_side(self, vehicle: ParsedVehicle) -> Optional[OrderSide]:
        raw_side = str(vehicle.side or "NONE").upper()
        if raw_side == "BUY":
            return OrderSide.BUY
        if raw_side == "SELL":
            return OrderSide.SELL
        return None
