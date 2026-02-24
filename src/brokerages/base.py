"""Backward-compatible brokerage interface export.

Use `src.brokerages.ports` for new code.
"""

from src.brokerages.ports import TradingBrokerPort


Brokerage = TradingBrokerPort
