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


from fastapi import Request

@app.api_route("/test-alert", methods=["GET", "POST"])
async def test_alert(request: Request):
    """
    Test endpoint for WhatsApp alert.
    Works for both GET (browser) and POST (API tools).
    """
    from app.messaging import send_test_message
    try:
        result = send_test_message()
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
