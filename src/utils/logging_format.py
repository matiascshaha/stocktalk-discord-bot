from typing import Any, Dict, List, Optional


def format_mode_summary(trading_config: Dict[str, Any]) -> str:
    return (
        "Modes: auto_trade={auto} | paper_trade={paper} | min_confidence={min_conf:.2f} | "
        "default_amount={amount:.2f} | market_orders={market}"
    ).format(
        auto=_flag(trading_config.get("auto_trade")),
        paper=_flag(trading_config.get("paper_trade")),
        min_conf=float(trading_config.get("min_confidence", 0.0)),
        amount=float(trading_config.get("default_amount", 0.0)),
        market=_flag(trading_config.get("use_market_orders")),
    )


def format_startup_status(user: Any, channel_id: Any, ai_provider: Optional[str], auto_trading: bool) -> List[str]:
    return [
        "Discord stock monitor active.",
        f"Logged in as: {user}",
        f"Monitoring channel: {channel_id}",
        f"AI parser: {ai_provider.title() if ai_provider else 'None (Regex only)'}",
        f"Auto-trading: {'ENABLED' if auto_trading else 'DISABLED'}",
    ]


def format_pick_summary(picks: List[Dict[str, Any]]) -> str:
    if not picks:
        return "No stock picks detected."

    tickers = [p.get("ticker") for p in picks if p.get("ticker")]
    actions = [p.get("action") for p in picks if p.get("action")]
    ticker_str = ", ".join(tickers) if tickers else "N/A"
    action_str = ", ".join(actions) if actions else "N/A"
    return f"Picks: count={len(picks)} | tickers={ticker_str} | actions={action_str}"


def _flag(value: Any) -> str:
    return "ON" if bool(value) else "OFF"
