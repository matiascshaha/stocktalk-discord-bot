from typing import Optional


def build_signal_payload(
    ticker: str,
    action: str = "BUY",
    confidence: float = 0.9,
    weight_percent: Optional[float] = 5.0,
    vehicles: Optional[list[dict]] = None,
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
        "vehicles": vehicles if vehicles is not None else [{"type": "STOCK", "enabled": True, "intent": intent, "side": side}],
    }
