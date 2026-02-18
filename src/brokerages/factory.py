"""Brokerage adapter factory."""

from typing import Optional

from src.brokerages.base import Brokerage
from src.brokerages.webull import WebullBroker
from src.webull_trader import WebullTrader


def build_brokerage(broker_key: str, trader: Optional[WebullTrader]) -> Brokerage:
    normalized = str(broker_key or "").strip().lower()
    if normalized == "webull":
        if trader is None:
            raise ValueError("Webull brokerage requires an initialized trader")
        return WebullBroker(trader)

    raise ValueError(f"Unsupported brokerage provider '{broker_key}'")
