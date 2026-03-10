"""Option sizing helpers for Webull option orders."""

from typing import Any, Callable, Dict, Optional

from src.models.webull_models import AccountBalanceResponse, OptionOrderRequest


class WebullOptionSizer:
    """Resolve option payloads from notional and weighting inputs."""

    def __init__(
        self,
        *,
        get_account_balance_contract: Callable[[], Optional[AccountBalanceResponse]],
        get_buying_power: Callable[..., Optional[float]],
        enforce_margin_buffer: Callable[[Optional[AccountBalanceResponse], float], None],
        build_v2_payload: Callable[[OptionOrderRequest, Optional[int]], Dict[str, Any]],
        estimate_contract_notional: Callable[[OptionOrderRequest], float],
    ):
        self._get_account_balance_contract = get_account_balance_contract
        self._get_buying_power = get_buying_power
        self._enforce_margin_buffer = enforce_margin_buffer
        self._build_v2_payload = build_v2_payload
        self._estimate_contract_notional = estimate_contract_notional

    def build_from_weighting(self, order: OptionOrderRequest, weighting: float) -> Dict[str, Any]:
        balance = self._get_account_balance_contract()
        buying_power = self._get_buying_power(balance=balance)
        if buying_power is None:
            raise ValueError("Unable to fetch buying power for option weighting calculation")
        target_notional = float(buying_power) * (float(weighting) / 100.0)
        if target_notional <= 0:
            raise ValueError("Computed option weighting notional must be positive")
        return self.build_from_notional(order, notional_dollar_amount=target_notional, balance=balance)

    def build_from_notional(
        self,
        order: OptionOrderRequest,
        *,
        notional_dollar_amount: float,
        balance: Optional[AccountBalanceResponse] = None,
    ) -> Dict[str, Any]:
        side = str(getattr(order.side, "value", order.side or "")).upper().strip()
        if side != "BUY":
            return self._build_v2_payload(order, None)

        target_notional = float(notional_dollar_amount)
        if target_notional <= 0:
            raise ValueError("Option notional sizing requires a positive notional amount")

        per_contract_notional = self._estimate_contract_notional(order)
        quantity = max(1, int(target_notional / per_contract_notional))
        estimated_trade_notional = per_contract_notional * float(quantity)
        self._enforce_margin_buffer(balance or self._get_account_balance_contract(), estimated_trade_notional)
        return self._build_v2_payload(order, quantity)
