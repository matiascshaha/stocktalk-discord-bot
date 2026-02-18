"""Canonical execution result contracts returned by broker adapters."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class OrderError(BaseModel):
    code: str
    message: str
    retryable: bool = False


class OrderResult(BaseModel):
    broker: str
    success: bool
    raw: Dict[str, Any] = Field(default_factory=dict)
    order_id: Optional[str] = None
    error: Optional[OrderError] = None
