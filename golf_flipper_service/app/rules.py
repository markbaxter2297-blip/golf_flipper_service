"""
Logic for computing resale values and risk ratings from configuration rules.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional

from .models import SourceItem

logger = logging.getLogger(__name__)

# Load rules on module import
RULES_PATH = Path(__file__).resolve().parent.parent / "rules.json"

try:
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        _rules = json.load(f)
except Exception as exc:
    logger.warning("Failed to load rules.json: %s", exc)
    _rules = {"default_multiplier": 1.5, "brands": {}, "items": []}


def _match_brand(title: str) -> Optional[str]:
    """Return the brand name from rules that appears in the title, case-insensitive."""
    t_lower = title.lower()
    for brand in _rules.get("brands", {}).keys():
        if brand.lower() in t_lower:
            return brand
    return None


def _match_item(title: str) -> Optional[Dict[str, str]]:
    """Return a specific item rule if both brand and model match the title."""
    t_lower = title.lower()
    for item_rule in _rules.get("items", []):
        brand = item_rule.get("brand", "").lower()
        model = item_rule.get("model", "").lower()
        if brand in t_lower and model in t_lower:
            return item_rule
    return None


def compute_resale_value(item: SourceItem) -> float:
    """Compute the expected resale value for an item based on the rules.

    The logic is:
    1. If a specific item rule matches (both brand and model), use its multiplier.
    2. Else if a brand-level multiplier exists, use that.
    3. Else use the default multiplier.
    """
    price = item.price
    if price <= 0:
        return 0.0

    rule = _match_item(item.title)
    if rule and "multiplier" in rule:
        mult = float(rule["multiplier"])
        return price * mult

    brand = _match_brand(item.title)
    if brand:
        mult = float(_rules["brands"].get(brand, _rules.get("default_multiplier", 1.5)))
        return price * mult

    mult = float(_rules.get("default_multiplier", 1.5))
    return price * mult


def compute_risk(seller_score: Optional[float], buyer_protection: float, shipping_cost: float) -> str:
    """Determine a risk tag based on available data.

    The heuristic used:
    - High risk if seller_score is missing or < 90, or if buyer_protection or shipping_cost are 0.
    - Low risk if seller_score >= 98.
    - Medium risk otherwise.
    """
    # missing or suspicious data
    if seller_score is None or seller_score < 90 or buyer_protection == 0 or shipping_cost == 0:
        return "High"
    if seller_score >= 98:
        return "Low"
    return "Medium"