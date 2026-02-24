from typing import Any, Dict, List, Optional


def format_mode_summary(trading_config: Dict[str, Any]) -> str:
    return (
        "Modes: broker={broker} | auto_trade={auto} | paper_trade={paper} | options_enabled={options} | "
        "min_confidence={min_conf:.2f} | default_amount={amount:.2f} | market_orders={market}"
    ).format(
        broker=str(trading_config.get("broker", "webull")).lower(),
        auto=_flag(trading_config.get("auto_trade")),
        paper=_flag(trading_config.get("paper_trade")),
        options=_flag(trading_config.get("options_enabled")),
        min_conf=float(trading_config.get("min_confidence", 0.0)),
        amount=float(trading_config.get("default_amount", 0.0)),
        market=_flag(trading_config.get("use_market_orders")),
    )


def format_startup_status(
    user: Any,
    channel_id: Any,
    ai_provider: Optional[str],
    auto_trading: bool,
    options_enabled: bool,
    contract_version: str,
) -> List[str]:
    return [
        "Discord stock monitor active.",
        f"Logged in as: {user}",
        f"Monitoring channel: {channel_id}",
        f"AI parser: {ai_provider.title() if ai_provider else 'None'}",
        f"Parser contract version: {contract_version}",
        f"Auto-trading: {'ENABLED' if auto_trading else 'DISABLED'}",
        f"Options execution: {'ENABLED' if options_enabled else 'DISABLED'}",
    ]


def format_pick_summary(parsed_message: Dict[str, Any]) -> str:
    signal_objs = parsed_message.get("signals", [])
    if not signal_objs:
        return "No actionable signals detected."

    tickers = [s.get("ticker") for s in signal_objs if isinstance(s, dict) and s.get("ticker")]
    actions = [s.get("action") for s in signal_objs if isinstance(s, dict) and s.get("action")]
    ticker_str = ", ".join(tickers) if tickers else "N/A"
    action_str = ", ".join(actions) if actions else "N/A"
    return f"Signals: count={len(signal_objs)} | tickers={ticker_str} | actions={action_str}"


def _flag(value: Any) -> str:
    return "ON" if bool(value) else "OFF"
