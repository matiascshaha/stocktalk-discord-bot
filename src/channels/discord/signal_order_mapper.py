"""Mapping helpers from parsed Discord signals into executable order contracts."""

from datetime import date, datetime, timedelta
from typing import Any, Optional

from src.models.parser_models import ParsedSignal
from src.trading.contracts import OptionOrder, OptionType, OrderSide, OrderType, StockOrder


class DiscordSignalOrderMapper:
    """Convert parser signals into stock/option order contracts under runtime config."""

    def __init__(self, *, trading_config: dict, logger: Any):
        self._trading_config = trading_config
        self._logger = logger

    def to_stock_order(self, signal: ParsedSignal) -> Optional[StockOrder]:
        stock_vehicle = next((vehicle for vehicle in signal.vehicles if vehicle.type == "STOCK"), None)
        if stock_vehicle is None:
            return None
        if not stock_vehicle.enabled or stock_vehicle.intent != "EXECUTE":
            return None
        if stock_vehicle.side == "NONE":
            self._logger.info("Skipping non-executable stock signal for %s", signal.ticker)
            return None

        side = OrderSide.SELL if stock_vehicle.side == "SELL" else OrderSide.BUY
        return StockOrder(symbol=signal.ticker, side=side, quantity=1)

    def to_option_orders(self, signal: ParsedSignal) -> list[OptionOrder]:
        option_orders: list[OptionOrder] = []
        for vehicle in signal.vehicles:
            order = self._option_vehicle_to_order(signal, vehicle)
            if order is not None:
                option_orders.append(order)
        return option_orders

    def min_confidence_threshold(self) -> float:
        try:
            return float(self._trading_config.get("min_confidence", 0.0))
        except (TypeError, ValueError):
            return 0.0

    def passes_min_confidence(self, signal: ParsedSignal) -> bool:
        return float(signal.confidence) >= self.min_confidence_threshold()

    def resolve_option_quantity(self, quantity_hint: Optional[float]) -> int:
        if quantity_hint is None:
            return 1
        try:
            quantity = int(float(quantity_hint))
        except (TypeError, ValueError):
            return 1
        return max(1, quantity)

    def resolve_option_order_type(self) -> OrderType:
        if bool(self._trading_config.get("use_market_orders", True)):
            return OrderType.MARKET
        return OrderType.LIMIT

    def resolve_option_limit_price(self, order_type: OrderType) -> Optional[float]:
        if order_type != OrderType.LIMIT:
            return None
        raw_value = self._trading_config.get("option_limit_price_without_quote")
        try:
            parsed = float(raw_value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    def resolve_time_in_force(self) -> str:
        candidate = str(self._trading_config.get("time_in_force", "DAY")).upper().strip()
        return candidate if candidate in {"DAY", "GTC", "IOC", "FOK"} else "DAY"

    def normalize_option_expiry(self, raw_expiry: Optional[str]) -> Optional[str]:
        if raw_expiry in (None, "", "null"):
            return None
        normalized = str(raw_expiry).strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%b %d %Y", "%B %d %Y", "%b %d, %Y", "%B %d, %Y"):
            try:
                return datetime.strptime(normalized, fmt).date().isoformat()
            except ValueError:
                continue

        for fmt in ("%b %Y", "%B %Y"):
            try:
                parsed = datetime.strptime(normalized, fmt)
                return self.third_friday(parsed.year, parsed.month).isoformat()
            except ValueError:
                continue
        return None

    @staticmethod
    def third_friday(year: int, month: int) -> date:
        first_day = date(year, month, 1)
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + timedelta(days=days_until_friday)
        return first_friday + timedelta(days=14)

    def _option_vehicle_to_order(self, signal: ParsedSignal, vehicle: Any) -> Optional[OptionOrder]:
        if vehicle.type != "OPTION":
            return None
        if not vehicle.enabled or vehicle.intent != "EXECUTE":
            return None
        if vehicle.side == "NONE":
            self._logger.info("Skipping non-executable option signal for %s", signal.ticker)
            return None
        if not vehicle.option_type or vehicle.strike is None:
            self._logger.info(
                "Skipping option signal for %s due to missing option_type/strike (option_type=%s, strike=%s)",
                signal.ticker,
                vehicle.option_type,
                vehicle.strike,
            )
            return None

        normalized_expiry = self.normalize_option_expiry(vehicle.expiry)
        if not normalized_expiry:
            self._logger.info(
                "Skipping option signal for %s due to unsupported expiry format: %s",
                signal.ticker,
                vehicle.expiry,
            )
            return None

        side = OrderSide.SELL if vehicle.side == "SELL" else OrderSide.BUY
        option_type = OptionType(str(vehicle.option_type).upper())
        order_type = self.resolve_option_order_type()
        limit_price = self.resolve_option_limit_price(order_type)
        if order_type == OrderType.LIMIT and limit_price is None:
            self._logger.info(
                "Skipping option signal for %s because no limit price is configured for LIMIT option orders.",
                signal.ticker,
            )
            return None

        return OptionOrder(
            symbol=signal.ticker,
            side=side,
            quantity=self.resolve_option_quantity(vehicle.quantity_hint),
            option_type=option_type,
            strike_price=float(vehicle.strike),
            option_expire_date=normalized_expiry,
            order_type=order_type,
            limit_price=limit_price,
            time_in_force=self.resolve_time_in_force(),
        )
