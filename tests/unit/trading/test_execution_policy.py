from unittest.mock import MagicMock

import pytest

from src.models.parser_models import ParsedSignal
from src.trading.policy import TradingExecutionPolicy
from tests.support.cases.trading_policy import TRADING_POLICY_CASES
from tests.support.payloads.signals import build_signal_payload


ACCOUNT_CONSTRAINTS = """
MARGIN CONSTRAINTS:
- Never let Margin Equity % fall below 35% after a trade.
- Do not place the trade if the resulting Margin Equity % would be < 35%.

TRADING RULES:
- Only execute LONG positions or PUT positions.
- No short selling.
""".strip()

TRADING_CONFIG = {
    "min_confidence": 0.7,
    "default_amount": 1000.0,
}


@pytest.mark.unit
@pytest.mark.parametrize("case", TRADING_POLICY_CASES, ids=lambda case: case.name)
def test_execution_policy_cases(case):
    policy = TradingExecutionPolicy(TRADING_CONFIG, ACCOUNT_CONSTRAINTS)
    signal = ParsedSignal.model_validate(
        build_signal_payload(
            "AAPL",
            action=case.action,
            confidence=case.confidence,
            weight_percent=case.weight_percent,
        )
    )

    trader = MagicMock()
    if case.margin_equity_percent is not None:
        trader.get_account_balance.return_value = {
            "total_market_value": 10000.0,
            "account_currency_assets": [
                {
                    "net_liquidation_value": 10000.0 * (case.margin_equity_percent / 100.0),
                    "margin_power": 5000.0,
                    "cash_power": 5000.0,
                }
            ],
        }

    decision = policy.evaluate(signal, trading_account=trader)

    assert decision.allowed is case.expected_allowed
    assert decision.reason == case.expected_reason
    assert policy.resolve_notional_dollar_amount(signal) == case.expected_notional_dollar_amount
