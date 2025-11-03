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
@app.get("/test-vinted")
async def test_vinted():
    """
    One-off Vinted probe using your ENV cookie with full browser-like headers.
    Accepts either:
      - raw session token (vinted_fr_session value), or
      - a full Cookie header string (key=value; key2=value2; ...)
    Returns first few item titles on success, or the exact HTTP error text.
    """
    import httpx

    base = "https://www.vinted.co.uk"
    # simple query to prove we can fetch – tweak if you like
    url = f"{base}/api/v2/catalog/items?search_text=golf&per_page=5&order=newest_first"

    cookie_value = settings.vinted_cookie.strip()
    # If user gave only the session token, build the Cookie header ourselves.
    if "=" not in cookie_value:
        cookie_header = f"vinted_fr_session={cookie_value}"
    else:
        # If user pasted a full cookie header, use it verbatim.
        cookie_header = cookie_value

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": f"{base}/",
        "Origin": base,
        "Connection": "keep-alive",
        "Cookie": cookie_header,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            r = await client.get(url, headers=headers)
            status = r.status_code
            text = r.text[:8000]  # cap output
            if r.headers.get("content-type", "").startswith("application/json"):
                data = r.json()
                items = data.get("items") or data.get("catalog_items") or []
                titles = [i.get("title") for i in items if isinstance(i, dict)]
                return {"status": status, "count": len(titles), "titles": titles[:5]}
            else:
                return {"status": status, "body": text}
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "detail": str(e),
            "trace": traceback.format_exc().splitlines()[-15:],
        }
