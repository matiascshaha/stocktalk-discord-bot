"""Parser output contract models.

These models are the canonical boundary between AI parsing and trading logic.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PickAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class PickUrgency(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PickSentiment(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class ParsedPick(BaseModel):
    """Normalized pick returned by parser and consumed by trading adapter."""

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    ticker: str = Field(..., min_length=1)
    action: PickAction = Field(default=PickAction.BUY)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    weight_percent: Optional[float] = Field(default=None)
    urgency: PickUrgency = Field(default=PickUrgency.MEDIUM)
    sentiment: PickSentiment = Field(default=PickSentiment.NEUTRAL)
    reasoning: str = Field(default="")

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value):
        ticker = str(value or "").upper().replace("$", "").strip()
        if not ticker:
            raise ValueError("ticker is required")
        return ticker

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, value):
        action = str(value or "BUY").upper().strip()
        return action if action in {"BUY", "SELL", "HOLD"} else "BUY"

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value):
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            confidence = 0.0
        return max(0.0, min(1.0, confidence))

    @field_validator("weight_percent", mode="before")
    @classmethod
    def normalize_weight_percent(cls, value):
        if value in ("", None):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @field_validator("urgency", mode="before")
    @classmethod
    def normalize_urgency(cls, value):
        urgency = str(value or "MEDIUM").upper().strip()
        return urgency if urgency in {"LOW", "MEDIUM", "HIGH"} else "MEDIUM"

    @field_validator("sentiment", mode="before")
    @classmethod
    def normalize_sentiment(cls, value):
        sentiment = str(value or "NEUTRAL").upper().strip()
        return sentiment if sentiment in {"BULLISH", "BEARISH", "NEUTRAL"} else "NEUTRAL"

    @field_validator("reasoning", mode="before")
    @classmethod
    def normalize_reasoning(cls, value):
        return str(value or "")


class ParserMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str = Field(default="ok")
    provider: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)


class ParsedMessage(BaseModel):
    """Top-level parser result contract."""

    model_config = ConfigDict(extra="allow")

    picks: List[ParsedPick] = Field(default_factory=list)
    meta: ParserMeta = Field(default_factory=ParserMeta)
