"""
Client for interacting with eBay's Browse API.
"""

from __future__ import annotations

import base64
import logging
import time
from typing import List

import httpx

from .config import settings
from .models import SourceItem

logger = logging.getLogger(__name__)


class EbayClient:
    """Simple client for eBay Buy Browse API."""

    def __init__(self) -> None:
        self.app_id = settings.ebay_app_id
        self.cert_id = settings.ebay_cert_id
        self.redirect_uri = settings.ebay_redirect_uri
        self.market_id = settings.ebay_market
        self.token: str | None = None
        self.token_expiry: float = 0.0

    async def _fetch_access_token(self) -> None:
        """Retrieve an access token using client credentials."""
        auth = base64.b64encode(f"{self.app_id}:{self.cert_id}".encode()).decode()
        url = "https://api.ebay.com/identity/v1/oauth2/token"
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.item.summary",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
        self.token = payload.get("access_token")
        expires_in = payload.get("expires_in", 7200)
        self.token_expiry = time.time() + expires_in - 60  # refresh one minute early
        logger.info("Obtained eBay access token; expires in %s seconds", expires_in)

    async def _ensure_token(self) -> str:
        """Ensure a valid token is available and return it."""
        if not self.token or time.time() >= self.token_expiry:
            await self._fetch_access_token()
        assert self.token is not None
        return self.token

    async def search_items(self, keywords: List[str], category_ids: List[str], limit: int = 20) -> List[SourceItem]:
        """Search for newly listed items matching the given keywords and categories."""
        token = await self._ensure_token()
        query = " ".join(keywords)
        category_param = ",".join(category_ids) if category_ids else None
        url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        params = {
            "q": query,
            "limit": str(limit),
            "sort": "newlyListed",
        }
        if category_param:
            params["category_ids"] = category_param
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": self.market_id,
            "Content-Type": "application/json",
        }
        items: List[SourceItem] = []
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.error("Error fetching eBay listings: %s", exc)
            return items

        for entry in data.get("itemSummaries", []):
            try:
                item_id = entry.get("itemId")
                title = entry.get("title") or ""
                web_url = entry.get("itemWebUrl") or entry.get("itemHref") or ""
                price = float(entry.get("price", {}).get("value", 0))
                # Buyer protection on eBay is typically included in price; set to 0 for now
                buyer_protection = 0.0
                shipping_cost = 0.0
                shipping_options = entry.get("shippingOptions") or []
                if shipping_options:
                    cost = shipping_options[0].get("shippingCost")
                    if cost and cost.get("value") is not None:
                        shipping_cost = float(cost["value"])
                seller = entry.get("seller", {})
                seller_score = None
                if seller:
                    try:
                        seller_score = float(seller.get("feedbackPercentage"))
                    except Exception:
                        seller_score = None
                listed_at = None
                if entry.get("itemCreationDate"):
                    listed_at = entry["itemCreationDate"]
                item = SourceItem(
                    id=item_id,
                    source="ebay",
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
                logger.debug("Error parsing eBay item: %s", exc)
        return items