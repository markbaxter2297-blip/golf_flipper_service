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
def health() -> dict[str, str]:
    return {"status": "ok"}

# test alert route that works for GET + POST
@app.get("/test-alert")
@app.post("/test-alert")
def test_alert():
    """Test endpoint for WhatsApp alert (works for browser GET + API POST)."""
    from app.messaging import send_test_message
    try:
        result = send_test_message()
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

