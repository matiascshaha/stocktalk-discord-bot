"""Webull brokerage adapter package."""

from typing import Any


__all__ = ["WebullBroker"]


def __getattr__(name: str) -> Any:
    if name == "WebullBroker":
        from src.brokerages.webull.broker import WebullBroker

        return WebullBroker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
