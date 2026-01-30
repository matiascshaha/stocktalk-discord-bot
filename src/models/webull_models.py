"""
Pydantic models for Webull trading.

Type-safe models for orders and account data.
Uses Pydantic V2 syntax.
"""

from typing import Optional, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid


# ============================================================================
# Enums
# ============================================================================

class OrderSide(str, Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class TimeInForce(str, Enum):
    """Time in force"""
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class TradingSession(str, Enum):
    """Trading session"""
    ALL = "ALL"  # Include extended hours
    CORE = "CORE"  # Regular hours only
    NIGHT = "NIGHT"  # Night trading only


class InstrumentType(str, Enum):
    """Instrument type"""
    EQUITY = "EQUITY"
    OPTION = "OPTION"


class OptionType(str, Enum):
    """Option type"""
    CALL = "CALL"
    PUT = "PUT"


# ============================================================================
# Order Request Models (Required - for creating orders)
# ============================================================================

class StockOrderRequest(BaseModel):
    """
    Stock order request model.
    
    Example:
        order = StockOrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10,
            order_type=OrderType.LIMIT,
            limit_price=150.0
        )
    """
    model_config = ConfigDict(use_enum_values=True)
    
    symbol: str = Field(..., description="Stock ticker symbol")
    side: OrderSide = Field(..., description="BUY or SELL")
    quantity: float = Field(..., gt=0, description="Number of shares")
    order_type: OrderType = Field(OrderType.MARKET, description="MARKET or LIMIT")
    limit_price: Optional[float] = Field(None, gt=0, description="Limit price (required for LIMIT orders)")
    time_in_force: TimeInForce = Field(TimeInForce.DAY, description="Time in force")
    trading_session: TradingSession = Field(TradingSession.CORE, description="Trading session")
    
    @field_validator('symbol')
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol: uppercase, remove $, trim whitespace"""
        return str(v).upper().replace("$", "").strip()
    
    @field_validator('limit_price')
    @classmethod
    def validate_limit_price(cls, v: Optional[float], info) -> Optional[float]:
        """Validate that limit_price is provided for LIMIT orders"""
        if info.data.get('order_type') == OrderType.LIMIT and v is None:
            raise ValueError("limit_price is required for LIMIT orders")
        return v


class OptionLeg(BaseModel):
    """Single option leg"""
    model_config = ConfigDict(use_enum_values=True)
    
    side: OrderSide = Field(..., description="BUY or SELL")
    quantity: str = Field(..., description="Number of contracts")
    symbol: str = Field(..., description="Underlying ticker")
    strike_price: str = Field(..., description="Strike price")
    option_expire_date: str = Field(..., description="Expiry date (YYYY-MM-DD)")
    instrument_type: str = Field("OPTION", description="Always OPTION")
    option_type: OptionType = Field(..., description="CALL or PUT")
    market: str = Field("US", description="Market")
    
    @field_validator('symbol')
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return str(v).upper().replace("$", "").strip()


class OptionOrderRequest(BaseModel):
    """
    Option order request matching Webull's structure.
    
    Example:
        order = OptionOrderRequest(
            combo_type="NORMAL",
            order_type=OrderType.LIMIT,
            quantity="1",
            limit_price="21.25",
            option_strategy="SINGLE",
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            entrust_type="QTY",
            legs=[
                OptionLeg(
                    side=OrderSide.BUY,
                    quantity="1",
                    symbol="TSLA",
                    strike_price="400",
                    option_expire_date="2025-11-26",
                    option_type=OptionType.CALL,
                    market="US"
                )
            ]
        )
    """
    model_config = ConfigDict(use_enum_values=True)
    
    client_order_id: Optional[str] = Field(None, description="Auto-generated if not provided")
    combo_type: str = Field("NORMAL", description="Order combo type")
    order_type: OrderType = Field(..., description="LIMIT or MARKET")
    quantity: str = Field(..., description="Total quantity")
    limit_price: Optional[str] = Field(None, description="Limit price (required for LIMIT)")
    option_strategy: str = Field("SINGLE", description="SINGLE or other strategies")
    side: OrderSide = Field(..., description="BUY or SELL")
    time_in_force: TimeInForce = Field(TimeInForce.GTC, description="Time in force")
    entrust_type: str = Field("QTY", description="Entrust type")
    legs: List[OptionLeg] = Field(..., min_length=1, description="Option legs")
    
    @field_validator('limit_price')
    @classmethod
    def validate_limit_price(cls, v: Optional[str], info) -> Optional[str]:
        if info.data.get('order_type') == OrderType.LIMIT and not v:
            raise ValueError("limit_price is required for LIMIT orders")
        return v
    
    def model_post_init(self, __context):
        """Auto-generate client_order_id if not provided"""
        if not self.client_order_id:
            self.client_order_id = uuid.uuid4().hex


# ============================================================================
# Response Models (Optional - helpers for parsing Webull responses)
# ============================================================================

class AccountBalance(BaseModel):
    """
    Account balance information (optional helper).
    
    You can use this to parse Webull's balance response,
    or just use the raw dict from get_account_balance().
    """
    model_config = ConfigDict(extra='allow')
    
    account_id: Optional[str] = None
    buying_power: Optional[float] = None
    cash: Optional[float] = None
    total_value: Optional[float] = None
    net_liquidation: Optional[float] = None


class Position(BaseModel):
    """
    Account position (optional helper).
    
    You can use this to parse Webull's position response,
    or just use the raw dict from get_account_positions().
    """
    model_config = ConfigDict(extra='allow')
    
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    average_cost: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    position_side: Optional[str] = None  # LONG or SHORT

class OrderPreviewResponse(BaseModel):
    """
    Order preview response from Webull.
    
    Returned by preview_stock_order() and preview_option_order().
    """
    model_config = ConfigDict(extra='allow')
    
    estimated_cost: Optional[str] = Field(None, description="Estimated cost in currency")
    estimated_transaction_fee: Optional[str] = Field(None, description="Estimated transaction fee")
    currency: Optional[str] = Field(None, description="Currency (USD, etc)")
    
    # Add other fields as you discover them from Webull's response
    buying_power_effect: Optional[str] = None
    estimated_commission: Optional[str] = None
    
    @property
    def cost_as_float(self) -> Optional[float]:
        """Helper to get estimated_cost as float"""
        try:
            return float(self.estimated_cost) if self.estimated_cost else None
        except (ValueError, TypeError):
            return None
    
    @property
    def fee_as_float(self) -> Optional[float]:
        """Helper to get estimated_transaction_fee as float"""
        try:
            return float(self.estimated_transaction_fee) if self.estimated_transaction_fee else None
        except (ValueError, TypeError):
            return None