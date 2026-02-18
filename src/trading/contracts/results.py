"""Canonical execution result contracts returned by broker adapters."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class OrderError:
    code: str
    message: str
    retryable: bool = False


@dataclass
class OrderResult:
    broker: str
    success: bool
    raw: Dict[str, Any] = field(default_factory=dict)
    order_id: Optional[str] = None
    error: Optional[OrderError] = None

