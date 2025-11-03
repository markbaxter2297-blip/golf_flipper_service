"""
Entry point for the FastAPI application.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict

from fastapi import FastAPI, HTTPException

from .config import settings
from .db import init_db
from .messaging import send_whatsapp_message, build_whatsapp_message
from .models import SourceItem, Evaluation
from .polling import poller


logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(title="Golf Flipper Service", version="1.0.0")


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize database and start background polling."""
    await init_db()
    # Start polling in background
    asyncio.create_task(poller.start())
    logger.info("Service started and polling scheduled.")


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/test-alert")
async def test_alert() -> Dict[str, str]:
    """Send a test alert to verify WhatsApp configuration."""
    try:
        # Construct a dummy SourceItem for test
        item = SourceItem(
            id="test",
            source="test",
            title="Sample Golf Item",
            url="https://example.com/golf-item",
            price=10.00,
            buyer_protection=1.00,
            shipping_cost=2.50,
            seller_score=99.0,
            listed_at=None,
        )
        total_cost = item.price + item.buyer_protection + item.shipping_cost
        resale_value = item.price * 1.5
        profit = resale_value - total_cost
        evaluation = Evaluation(
            item=item,
            total_cost=total_cost,
            resale_value=resale_value,
            profit=profit,
            risk="Low",
        )
        message = build_whatsapp_message(evaluation)
        await send_whatsapp_message(message)
        return {"message": "Test alert sent."}
    except Exception as exc:
        logger.error("Failed to send test alert: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to send test alert")