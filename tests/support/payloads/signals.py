from typing import Any, List, Optional


def build_signal_payload(
    ticker: str,
    action: str = "BUY",
    confidence: float = 0.9,
    weight_percent: Optional[float] = 5.0,
    vehicles: Optional[List[dict[str, Any]]] = None,
):
    if vehicles is None:
        side = action if action in {"BUY", "SELL"} else "NONE"
        intent = "EXECUTE" if action in {"BUY", "SELL"} else "INFO"
        vehicles = [{"type": "STOCK", "enabled": True, "intent": intent, "side": side}]

    return {
        "ticker": ticker,
        "action": action,
        "confidence": confidence,
        "weight_percent": weight_percent,
        "urgency": "MEDIUM",
        "sentiment": "BULLISH" if action != "SELL" else "BEARISH",
        "reasoning": "test",
        "is_actionable": action in {"BUY", "SELL", "HOLD"},
        "vehicles": vehicles,
    }
