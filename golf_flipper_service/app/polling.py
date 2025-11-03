"""
Background polling tasks for fetching marketplace listings and sending notifications.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import settings
from .db import add_alert, add_item, alert_sent, item_exists
from .ebay import EbayClient
from .messaging import build_whatsapp_message, send_whatsapp_message
from .models import Evaluation, SourceItem
from .rules import compute_resale_value, compute_risk
from .vinted import VintedClient

logger = logging.getLogger(__name__)


class Poller:
    """Central orchestrator for polling marketplaces and sending notifications."""

    def __init__(self) -> None:
        self.ebay_client = EbayClient()
        self.vinted_client = VintedClient()
        self.scheduler = AsyncIOScheduler()

    async def poll_once(self) -> None:
        """Perform a single polling cycle."""
        keywords = settings.keywords
        logger.info("Polling marketplaces for keywords: %s", ", ".join(keywords))

        tasks: List[asyncio.Task[List[SourceItem]]] = []
        # Fetch concurrently
        tasks.append(asyncio.create_task(self.ebay_client.search_items(keywords, settings.ebay_category_ids)))
        tasks.append(asyncio.create_task(self.vinted_client.search_items(keywords)))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        items: List[SourceItem] = []
        for res in results:
            if isinstance(res, Exception):
                logger.error("Error fetching marketplace listings: %s", res)
            else:
                items.extend(res)
        logger.info("Fetched %d new items", len(items))

        # Process items sequentially to avoid DB race conditions
        for item in items:
            try:
                # Skip if we've processed this item before
                if await item_exists(item.id, item.source):
                    continue
                # Persist new item
                await add_item(
                    item.id,
                    item.source,
                    item.title,
                    item.url,
                    item.price,
                    item.buyer_protection,
                    item.shipping_cost,
                    item.seller_score,
                    item.listed_at,
                )

                total_cost = item.price + item.buyer_protection + item.shipping_cost
                resale_value = compute_resale_value(item)
                profit = resale_value - total_cost
                risk = compute_risk(item.seller_score, item.buyer_protection, item.shipping_cost)
                evaluation = Evaluation(
                    item=item,
                    total_cost=total_cost,
                    resale_value=resale_value,
                    profit=profit,
                    risk=risk,
                )
                # If profit meets threshold, notify
                if profit >= settings.profit_threshold_gbp:
                    # Check if alert already sent
                    if await alert_sent(item.id, item.source):
                        continue
                    message = build_whatsapp_message(evaluation)
                    await send_whatsapp_message(message)
                    await add_alert(item.id, item.source)
                    logger.info(
                        "Alert sent for %s %s with profit £%.2f",
                        item.source,
                        item.id,
                        profit,
                    )
            except Exception as exc:
                logger.error("Error processing item %s: %s", item.id, exc)

    async def start(self) -> None:
        """Initialize the scheduler and start polling at the configured interval."""
        # Kick off immediate polling on startup
        await self.poll_once()
        # Schedule recurring polling
        self.scheduler.add_job(self.poll_once, "interval", seconds=settings.poll_interval_seconds, id="poller")
        self.scheduler.start()


poller: Poller = Poller()