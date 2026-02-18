from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class TradingPolicyCase:
    name: str
    action: str
    confidence: float
    weight_percent: Optional[float]
    margin_equity_percent: Optional[float]
    expected_allowed: bool
    expected_reason: str
    expected_notional_dollar_amount: Optional[float]


TRADING_POLICY_CASES: Tuple[TradingPolicyCase, ...] = (
    TradingPolicyCase(
        name="allows_buy_with_weighting",
        action="BUY",
        confidence=0.95,
        weight_percent=5.0,
        margin_equity_percent=50.0,
        expected_allowed=True,
        expected_reason="allowed",
        expected_notional_dollar_amount=None,
    ),
    TradingPolicyCase(
        name="blocks_below_min_confidence",
        action="BUY",
        confidence=0.6,
        weight_percent=5.0,
        margin_equity_percent=50.0,
        expected_allowed=False,
        expected_reason="below_min_confidence",
        expected_notional_dollar_amount=None,
    ),
    TradingPolicyCase(
        name="blocks_margin_equity_below_threshold",
        action="BUY",
        confidence=0.95,
        weight_percent=5.0,
        margin_equity_percent=30.0,
        expected_allowed=False,
        expected_reason="margin_equity_below_minimum",
        expected_notional_dollar_amount=None,
    ),
    TradingPolicyCase(
        name="blocks_stock_sell_when_no_short_rule_present",
        action="SELL",
        confidence=0.95,
        weight_percent=5.0,
        margin_equity_percent=50.0,
        expected_allowed=False,
        expected_reason="shorting_disallowed_by_policy",
        expected_notional_dollar_amount=None,
    ),
    TradingPolicyCase(
        name="uses_default_notional_when_weight_missing",
        action="BUY",
        confidence=0.95,
        weight_percent=None,
        margin_equity_percent=50.0,
        expected_allowed=True,
        expected_reason="allowed",
        expected_notional_dollar_amount=1000.0,
    ),
)

