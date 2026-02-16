def build_signal_payload(
    ticker: str,
    action: str = "BUY",
    confidence: float = 0.9,
    weight_percent: float | None = 5.0,
):
    side = action if action in {"BUY", "SELL"} else "NONE"
    intent = "EXECUTE" if action in {"BUY", "SELL"} else "INFO"
    return {
        "ticker": ticker,
        "action": action,
        "confidence": confidence,
        "weight_percent": weight_percent,
        "urgency": "MEDIUM",
        "sentiment": "BULLISH" if action != "SELL" else "BEARISH",
        "reasoning": "test",
        "is_actionable": action in {"BUY", "SELL", "HOLD"},
        "vehicles": [{"type": "STOCK", "enabled": True, "intent": intent, "side": side}],
    }
