"""Canonical parser contract models.

This is the single source of truth for normalized parser output consumed by runtime.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


CONTRACT_VERSION = "1.0"


class PickAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NONE = "NONE"


class PickUrgency(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PickSentiment(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class VehicleType(str, Enum):
    STOCK = "STOCK"
    OPTION = "OPTION"


class VehicleIntent(str, Enum):
    EXECUTE = "EXECUTE"
    WATCH = "WATCH"
    INFO = "INFO"


class VehicleSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NONE = "NONE"


class OptionType(str, Enum):
    CALL = "CALL"
    PUT = "PUT"


class ParsedVehicle(BaseModel):
    """Trade vehicle derived from a signal (stock/options)."""

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    type: VehicleType
    enabled: bool = Field(default=True)
    intent: VehicleIntent = Field(default=VehicleIntent.INFO)
    side: VehicleSide = Field(default=VehicleSide.NONE)

    option_type: Optional[OptionType] = Field(default=None)
    strike: Optional[float] = Field(default=None)
    expiry: Optional[str] = Field(default=None)
    quantity_hint: Optional[float] = Field(default=None)

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, value):
        raw = str(value or "STOCK").upper().strip()
        return raw if raw in {"STOCK", "OPTION"} else "STOCK"

    @field_validator("intent", mode="before")
    @classmethod
    def normalize_intent(cls, value):
        raw = str(value or "INFO").upper().strip()
        return raw if raw in {"EXECUTE", "WATCH", "INFO"} else "INFO"

    @field_validator("side", mode="before")
    @classmethod
    def normalize_side(cls, value):
        raw = str(value or "NONE").upper().strip()
        return raw if raw in {"BUY", "SELL", "NONE"} else "NONE"

    @field_validator("option_type", mode="before")
    @classmethod
    def normalize_option_type(cls, value):
        if value in (None, "", "null"):
            return None
        raw = str(value).upper().strip()
        return raw if raw in {"CALL", "PUT"} else None

    @field_validator("strike", mode="before")
    @classmethod
    def normalize_strike(cls, value):
        if value in (None, "", "null"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @field_validator("quantity_hint", mode="before")
    @classmethod
    def normalize_quantity_hint(cls, value):
        if value in (None, "", "null"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class ParsedSignal(BaseModel):
    """Ticker-level signal extracted from a message."""

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    ticker: str = Field(..., min_length=1)
    action: PickAction = Field(default=PickAction.NONE)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = Field(default="")
    weight_percent: Optional[float] = Field(default=None)
    urgency: PickUrgency = Field(default=PickUrgency.MEDIUM)
    sentiment: PickSentiment = Field(default=PickSentiment.NEUTRAL)
    is_actionable: bool = Field(default=False)
    vehicles: List[ParsedVehicle] = Field(default_factory=list)

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
        raw = str(value or "NONE").upper().strip()
        return raw if raw in {"BUY", "SELL", "HOLD", "NONE"} else "NONE"

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
        if value in (None, "", "null"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @field_validator("urgency", mode="before")
    @classmethod
    def normalize_urgency(cls, value):
        raw = str(value or "MEDIUM").upper().strip()
        return raw if raw in {"LOW", "MEDIUM", "HIGH"} else "MEDIUM"

    @field_validator("sentiment", mode="before")
    @classmethod
    def normalize_sentiment(cls, value):
        raw = str(value or "NEUTRAL").upper().strip()
        return raw if raw in {"BULLISH", "BEARISH", "NEUTRAL"} else "NEUTRAL"

    @field_validator("reasoning", mode="before")
    @classmethod
    def normalize_reasoning(cls, value):
        return str(value or "")


class ParserSource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    author: Optional[str] = Field(default=None)
    channel_id: Optional[str] = Field(default=None)
    message_id: Optional[str] = Field(default=None)
    message_text: Optional[str] = Field(default=None)


class ParserMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str = Field(default="ok")
    provider: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)
    warnings: List[str] = Field(default_factory=list)


class ParsedMessage(BaseModel):
    """Top-level parser result contract."""

    model_config = ConfigDict(extra="ignore")

    contract_version: str = Field(default=CONTRACT_VERSION)
    source: ParserSource = Field(default_factory=ParserSource)
    signals: List[ParsedSignal] = Field(default_factory=list)
    meta: ParserMeta = Field(default_factory=ParserMeta)
