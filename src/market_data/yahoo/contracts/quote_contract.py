"""Pydantic contracts for Yahoo quote-shape probe payloads."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class YahooQuoteSampleValues(BaseModel):
    """Subset of quote-like scalar values captured from Yahoo payloads."""

    model_config = ConfigDict(extra="forbid")

    bid: Optional[float] = None
    ask: Optional[float] = None
    last_price: Optional[float] = Field(default=None, alias="lastPrice")
    regular_market_price: Optional[float] = Field(default=None, alias="regularMarketPrice")
    current_price: Optional[float] = Field(default=None, alias="currentPrice")
    previous_close: Optional[float] = Field(default=None, alias="previousClose")

    @field_validator(
        "bid",
        "ask",
        "last_price",
        "regular_market_price",
        "current_price",
        "previous_close",
        mode="before",
    )
    @classmethod
    def normalize_float(cls, value):
        if value in (None, "", "null"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def has_usable_price(self) -> bool:
        for candidate in (
            self.last_price,
            self.regular_market_price,
            self.current_price,
            self.bid,
            self.ask,
            self.previous_close,
        ):
            if candidate is not None and candidate > 0:
                return True
        return False


class YahooQuotePricePresence(BaseModel):
    """Boolean field-presence map for selected Yahoo quote fields."""

    model_config = ConfigDict(extra="forbid")

    bid: bool
    ask: bool
    last_price: bool = Field(alias="lastPrice")
    regular_market_price: bool = Field(alias="regularMarketPrice")
    current_price: bool = Field(alias="currentPrice")
    previous_close: bool = Field(alias="previousClose")


class YahooQuoteShape(BaseModel):
    """Contract for trimmed quote-shape capture from live Yahoo probe."""

    model_config = ConfigDict(extra="forbid")

    fast_info_keys: list[str]
    info_keys_count: int = Field(ge=0)
    info_keys_sample: list[str]
    sample_values: YahooQuoteSampleValues
    price_fields_present: YahooQuotePricePresence

