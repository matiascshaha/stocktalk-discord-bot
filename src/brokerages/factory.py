"""Broker adapter factory for runtime selection from config."""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.brokerages.composite import CompositeTradingBroker
from src.brokerages.ports import MarketDataPort, TradingBrokerPort
from src.brokerages.provider_registry import (
    resolve_execution_provider_name,
    resolve_quote_provider_name,
    validate_provider_split,
)
from src.brokerages.webull import WebullBroker
from src.market_data.yahoo import YahooQuoteProvider
from src.utils.logger import setup_logger
from src.webull_trader import WebullTrader


logger = setup_logger("broker_factory")


@dataclass
class BrokerRuntime:
    broker: TradingBrokerPort
    trading_account: Optional[Any] = None


def create_broker_runtime(
    trading_config: Dict[str, Any],
    webull_config: Dict[str, Any],
    public_config: Optional[Dict[str, Any]] = None,
) -> Optional[BrokerRuntime]:
    _ = public_config
    if not bool(trading_config.get("auto_trade", False)):
        return None

    execution_provider = resolve_execution_provider_name(trading_config)
    quote_provider = resolve_quote_provider_name(trading_config, execution_provider)
    validation_errors = validate_provider_split(execution_provider, quote_provider)
    if validation_errors:
        raise ValueError("; ".join(validation_errors))

    execution_runtime = _build_execution_runtime(execution_provider, trading_config, webull_config)
    if execution_runtime is None:
        return None

    if quote_provider == execution_provider:
        return execution_runtime

    logger.info(
        "Initializing split provider runtime (execution=%s, quotes=%s).",
        execution_provider,
        quote_provider,
    )
    quote_adapter = _build_quote_provider(
        quote_provider=quote_provider,
        execution_provider=execution_provider,
        execution_runtime=execution_runtime,
    )
    return BrokerRuntime(
        broker=CompositeTradingBroker(
            execution_broker=execution_runtime.broker,
            quote_provider=quote_adapter,
        ),
        trading_account=execution_runtime.trading_account,
    )


def _build_execution_runtime(
    execution_provider: str,
    trading_config: Dict[str, Any],
    webull_config: Dict[str, Any],
) -> Optional[BrokerRuntime]:
    if execution_provider == "webull":
        return _build_webull_runtime(trading_config, webull_config)
    raise ValueError(f"Unsupported trading execution provider '{execution_provider}'")


def _build_quote_provider(
    quote_provider: str,
    execution_provider: str,
    execution_runtime: BrokerRuntime,
) -> MarketDataPort:
    if quote_provider == "yahoo":
        return YahooQuoteProvider()
    if quote_provider == "webull":
        if execution_provider == "webull":
            return execution_runtime.broker
        raise ValueError("Webull quote provider currently requires execution_provider=webull")
    raise ValueError(f"Unsupported trading quote provider '{quote_provider}'")


def _build_webull_runtime(trading_config: Dict[str, Any], webull_config: Dict[str, Any]) -> Optional[BrokerRuntime]:
    paper_trade = bool(trading_config.get("paper_trade", False))
    app_key = webull_config.get("test_app_key") if paper_trade else webull_config.get("app_key") or os.getenv("WEBULL_APP_KEY")
    app_secret = webull_config.get("test_app_secret") if paper_trade else webull_config.get("app_secret") or os.getenv("WEBULL_APP_SECRET")
    account_id = (
        webull_config.get("test_account_id")
        or webull_config.get("webull_test_account_id")
        if paper_trade
        else webull_config.get("account_id") or os.getenv("WEBULL_ACCOUNT_ID")
    )

    if not app_key or not app_secret:
        raise ValueError(
            "Webull credentials are required when trading.execution_provider=webull and auto_trade=true"
        )

    logger.info("Initializing Webull trader adapter.")
    trader = WebullTrader(
        app_key=app_key,
        app_secret=app_secret,
        paper_trade=paper_trade,
        region=str(webull_config.get("region", "US")),
        account_id=account_id,
    )

    if not trader.login():
        logger.warning("Webull login failed; continuing in monitor-only mode.")
        return None

    return BrokerRuntime(
        broker=WebullBroker(trader),
        trading_account=trader,
    )
