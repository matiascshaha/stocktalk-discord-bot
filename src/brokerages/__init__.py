"""Brokerage integrations and runtime ports."""

from typing import Any


__all__ = ["BrokerRuntime", "TradingBrokerPort", "create_broker_runtime"]


def __getattr__(name: str) -> Any:
    if name == "TradingBrokerPort":
        from src.brokerages.ports import TradingBrokerPort

        return TradingBrokerPort
    if name in {"BrokerRuntime", "create_broker_runtime"}:
        from src.brokerages.factory import BrokerRuntime, create_broker_runtime

        if name == "BrokerRuntime":
            return BrokerRuntime
        return create_broker_runtime
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
