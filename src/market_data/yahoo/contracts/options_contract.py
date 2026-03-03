"""Pydantic contracts for Yahoo options-chain probe payloads."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class YahooOptionContractSample(BaseModel):
    """Subset of option-contract fields captured from Yahoo chain rows."""

    model_config = ConfigDict(extra="forbid")

    contract_symbol: Optional[str] = Field(default=None, alias="contractSymbol")
    strike: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    last_price: Optional[float] = Field(default=None, alias="lastPrice")
    volume: Optional[float] = None
    open_interest: Optional[float] = Field(default=None, alias="openInterest")
    implied_volatility: Optional[float] = Field(default=None, alias="impliedVolatility")
    in_the_money: Optional[float] = Field(default=None, alias="inTheMoney")

    @field_validator(
        "strike",
        "bid",
        "ask",
        "last_price",
        "volume",
        "open_interest",
        "implied_volatility",
        "in_the_money",
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


class YahooOptionTableShape(BaseModel):
    """Contract for one side (calls/puts) of a Yahoo options-chain shape."""

    model_config = ConfigDict(extra="forbid")

    row_count: int = Field(ge=0)
    columns: list[str]
    sample: YahooOptionContractSample = Field(default_factory=YahooOptionContractSample)


class YahooOptionChainShape(BaseModel):
    """Contract for trimmed options-chain shape capture from live Yahoo probe."""

    model_config = ConfigDict(extra="forbid")

    calls: YahooOptionTableShape
    puts: YahooOptionTableShape

