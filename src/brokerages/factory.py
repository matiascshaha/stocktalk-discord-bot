"""Broker adapter factory for runtime selection from config."""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.brokerages.ports import TradingBrokerPort
from src.brokerages.public import PublicBroker
from src.brokerages.webull import WebullBroker
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
    if not bool(trading_config.get("auto_trade", False)):
        return None

    broker_name = str(trading_config.get("broker", "webull")).strip().lower()
    if broker_name == "webull":
        return _build_webull_runtime(trading_config, webull_config)

    if broker_name == "public":
        logger.info("Initializing Public broker adapter scaffold.")
        return BrokerRuntime(broker=PublicBroker(public_config or {}))

    raise ValueError(f"Unsupported trading broker '{broker_name}'")


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
        raise ValueError("Webull credentials are required when trading.broker=webull and auto_trade=true")

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

