"""Stock order planning and execution modules."""

__all__ = [
    "OptionOrderExecutor",
    "SignalOrderRouter",
    "StockOrderExecutionPlanner",
    "StockOrderExecutor",
]


def __getattr__(name):
    if name == "StockOrderExecutor":
        from src.trading.orders.executor import StockOrderExecutor

        return StockOrderExecutor
    if name == "StockOrderExecutionPlanner":
        from src.trading.orders.planner import StockOrderExecutionPlanner

        return StockOrderExecutionPlanner
    if name == "OptionOrderExecutor":
        from src.trading.orders.option_executor import OptionOrderExecutor

        return OptionOrderExecutor
    if name == "SignalOrderRouter":
        from src.trading.orders.router import SignalOrderRouter

        return SignalOrderRouter
    raise AttributeError(f"module 'src.trading.orders' has no attribute {name!r}")
