"""Execution pricing models."""

from dataclasses import dataclass
from enum import Enum


class ExecutionUrgency(str, Enum):
    """Urgency level for execution-price selection."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class BestBidAskQuote:
    """Top-of-book quote used for limit-price calculations."""

    bid: float
    ask: float

