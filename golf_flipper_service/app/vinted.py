"""
Client for fetching new items from Vinted's public API.

Vinted does not offer an official public API; this client uses the same endpoints consumed by
the web application. A valid session cookie is required if access is restricted.
"""

from __future__ import annotations

import logging
from typing import List

import httpx

from .config import settings
from .models import SourceItem

logger = logging.getLogger(__name__)


class VintedClient:
    """Simple client for Vinted search."""

    def __init__(self) -> None:
        self.base_url = settings.vinted_base_url.rstrip("/")
        self.cookie = settings.vinted_cookie

    async def search_items(self, keywords: List[str], limit: int = 20) -> List[SourceItem]:
        """Search for new items on Vinted matching the keywords."""
        if not settings.vinted_enabled:
            return []
        query = " ".join(keywords)
        url = f"{self.base_url}/api/v2/catalog/items"
        params = {
            "search_text": query,
            "per_page": str(limit),
            "order": "newest_first",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; GolfFlipper/1.0; +https://example.com)",
            "Accept": "application/json, text/plain, */*",
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        items: List[SourceItem] = []
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.error("Error fetching Vinted listings: %s", exc)
            return items

        for entry in data.get("items", []):
            try:
                item_id = str(entry.get("id"))
                title = entry.get("title") or ""
                # Price is provided as numeric string; convert to float
                price = 0.0
                price_field = entry.get("price") or entry.get("price_amount")
                try:
                    price = float(price_field)
                except Exception:
                    try:
                        price = float(entry.get("price", {}).get("amount", 0))
                    except Exception:
                        price = 0.0
                # buyer protection: approximate formula 5% + £0.70
                buyer_protection = round(price * 0.05 + 0.70, 2) if price > 0 else 0.0
                # shipping cost if available
                shipping_cost = 0.0
                delivery_price = entry.get("delivery_price") or entry.get("delivery_fee")
                if delivery_price:
                    try:
                        shipping_cost = float(delivery_price)
                    except Exception:
                        try:
                            shipping_cost = float(delivery_price.get("amount"))
                        except Exception:
                            shipping_cost = 0.0
                seller_score = None  # Vinted does not expose feedback percentage publicly
                # Compose URL
                url_path = entry.get("url") or f"/items/{item_id}"
                web_url = url_path if url_path.startswith("http") else f"{self.base_url}{url_path}"
                listed_at = entry.get("created_at")
                item = SourceItem(
                    id=item_id,
                    source="vinted",
                    title=title,
                    url=web_url,
                    price=price,
                    buyer_protection=buyer_protection,
                    shipping_cost=shipping_cost,
                    seller_score=seller_score,
                    listed_at=listed_at,
                )
                items.append(item)
            except Exception as exc:
                logger.debug("Error parsing Vinted item: %s", exc)
        return items