"""
Domain models for marketplace items and alerts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SourceItem:
    """Represents a listing fetched from a marketplace."""

    id: str
    source: str  # e.g. "ebay" or "vinted"
    title: str
    url: str
    price: float
    buyer_protection: float
    shipping_cost: float
    seller_score: Optional[float]
    listed_at: Optional[datetime]


@dataclass
class Evaluation:
    """Results of evaluating a listing for potential profit."""

    item: SourceItem
    total_cost: float
    resale_value: float
    profit: float
    risk: str