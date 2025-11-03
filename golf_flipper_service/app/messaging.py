"""
WhatsApp messaging utilities using Meta's Cloud API.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from .config import settings
from .models import Evaluation

logger = logging.getLogger(__name__)


async def send_whatsapp_message(body: str) -> None:
    """Send a text message via WhatsApp Cloud API."""
    url = (
        f"https://graph.facebook.com/v17.0/{settings.whatsapp_phone_number_id}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": settings.whatsapp_to_msisdn.replace("+", ""),
        "type": "text",
        "text": {
            "preview_url": False,
            "body": body,
        },
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
        logger.info("Sent WhatsApp message to %s", settings.whatsapp_to_msisdn)
    except Exception as exc:
        logger.error("Failed to send WhatsApp message: %s", exc)


def build_whatsapp_message(eval: Evaluation) -> str:
    """Build a WhatsApp message body from evaluation data."""
    item = eval.item
    message = (
        f"New Flip Alert\n"
        f"Title: {item.title}\n"
        f"Link: {item.url}\n\n"
        f"Costs\n"
        f"Product: £{item.price:.2f}\n"
        f"Buyer protection: £{item.buyer_protection:.2f}\n"
        f"Shipping: £{item.shipping_cost:.2f}\n"
        f"Total: £{eval.total_cost:.2f}\n\n"
        f"Potential resale: £{eval.resale_value:.2f}\n"
        f"Estimated profit: £{eval.profit:.2f}  [{eval.risk}]"
    )
    return message