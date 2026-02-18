"""Runtime execution policy guards for parser-driven trades."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from src.models.parser_models import ParsedSignal


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def _to_float(raw_value: Any, default: float) -> float:
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default


def _extract_min_margin_equity_percent(account_constraints: str) -> Optional[float]:
    if not account_constraints:
        return None

    matches = []
    matches.extend(
        re.findall(
            r"margin\s+equity[\s\S]{0,120}?(?:below|<)\s*(\d+(?:\.\d+)?)\s*%",
            account_constraints,
            flags=re.IGNORECASE,
        )
    )
    matches.extend(
        re.findall(
            r"minimum\s+margin[\s\S]{0,80}?(\d+(?:\.\d+)?)\s*%",
            account_constraints,
            flags=re.IGNORECASE,
        )
    )
    if not matches:
        return None
    return max(float(value) for value in matches)


def _has_no_short_rule(account_constraints: str) -> bool:
    lowered = (account_constraints or "").lower()
    return any(
        token in lowered
        for token in (
            "no short",
            "no short selling",
            "only execute long positions",
            "only long positions",
        )
    )


def _current_margin_equity_percent(trading_account: Any) -> Optional[float]:
    if trading_account is None:
        return None

    try:
        account_balance = trading_account.get_account_balance()
        total_market_value = float(account_balance.get("total_market_value"))
        assets = account_balance.get("account_currency_assets") or []
        currency_asset = assets[0]
        net_liquidation_value = float(currency_asset.get("net_liquidation_value"))
    except Exception:
        return None

    if total_market_value <= 0:
        return 100.0
    return net_liquidation_value / total_market_value * 100.0


class TradingExecutionPolicy:
    """Policy checks that must pass before dispatching executable orders."""

    def __init__(self, trading_config: Mapping[str, Any], account_constraints: str):
        self._min_confidence = _to_float(trading_config.get("min_confidence"), 0.7)
        self._default_amount = max(0.0, _to_float(trading_config.get("default_amount"), 1000.0))
        self._min_margin_equity_percent = _extract_min_margin_equity_percent(account_constraints)
        self._no_short_rule = _has_no_short_rule(account_constraints)

    def evaluate(self, signal: ParsedSignal, trading_account: Any = None) -> PolicyDecision:
        action = str(signal.action)
        if action not in {"BUY", "SELL"}:
            return PolicyDecision(allowed=False, reason="non_executable_action")

        if signal.confidence < self._min_confidence:
            return PolicyDecision(allowed=False, reason="below_min_confidence")

        if self._no_short_rule and self._has_executable_stock_sell(signal):
            return PolicyDecision(allowed=False, reason="shorting_disallowed_by_policy")

        if action == "BUY" and self._min_margin_equity_percent is not None:
            margin_equity = _current_margin_equity_percent(trading_account)
            if margin_equity is not None and margin_equity < self._min_margin_equity_percent:
                return PolicyDecision(allowed=False, reason="margin_equity_below_minimum")

        return PolicyDecision(allowed=True, reason="allowed")

    def resolve_notional_dollar_amount(self, signal: ParsedSignal) -> Optional[float]:
        if str(signal.action) != "BUY":
            return None
        if signal.weight_percent is not None:
            return None
        return self._default_amount if self._default_amount > 0 else None

    def _has_executable_stock_sell(self, signal: ParsedSignal) -> bool:
        for vehicle in signal.vehicles:
            if (
                str(vehicle.type) == "STOCK"
                and bool(vehicle.enabled)
                and str(vehicle.intent) == "EXECUTE"
                and str(vehicle.side) == "SELL"
            ):
                return True
        return False
