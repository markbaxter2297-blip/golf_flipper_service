"""
Entry point for the FastAPI application.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict

from fastapi import FastAPI, HTTPException, Response

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
def health() -> dict[str, str]:
    return {"status": "ok"}

# GET + POST test route that sends a real WhatsApp message
@app.get("/test-alert")
@app.post("/test-alert")
async def test_alert():
    """
    Test endpoint for WhatsApp alert (works in browser + POST tools).
    """
    try:
        await send_whatsapp_message("GOLF FLIPPER TEST ALERT ✅")
        return {"status": "ok"}
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        # show full error
        return Response(
            content=f"ERROR: {e}\n\n{tb}",
            media_type="text/plain",
            status_code=500,
        )
