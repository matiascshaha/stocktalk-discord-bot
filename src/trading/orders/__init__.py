"""Stock order planning and execution modules."""

from typing import Any


__all__ = ["StockOrderExecutionPlanner", "StockOrderExecutor"]


def __getattr__(name: str) -> Any:
    if name == "StockOrderExecutor":
        from src.trading.orders.executor import StockOrderExecutor

        return StockOrderExecutor
    if name == "StockOrderExecutionPlanner":
        from src.trading.orders.planner import StockOrderExecutionPlanner

        return StockOrderExecutionPlanner
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
