"""
SQLite database utilities for storing processed items and sent alerts.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

import aiosqlite

from .config import settings


DB_PATH = settings.db_path


async def init_db() -> None:
    """Initialize the SQLite database with required tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT,
                url TEXT,
                price REAL,
                buyer_protection REAL,
                shipping_cost REAL,
                seller_score REAL,
                listed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, source)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                item_id TEXT NOT NULL,
                source TEXT NOT NULL,
                sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (item_id, source)
            )
            """
        )
        await db.commit()


async def item_exists(item_id: str, source: str) -> bool:
    """Check whether an item from a given source has already been processed."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM items WHERE id = ? AND source = ?", (item_id, source)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None


async def add_item(
    item_id: str,
    source: str,
    title: str,
    url: str,
    price: float,
    buyer_protection: float,
    shipping_cost: float,
    seller_score: Optional[float],
    listed_at: Optional[str],
) -> None:
    """Insert a new item into the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO items (id, source, title, url, price, buyer_protection, shipping_cost, seller_score, listed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item_id, source, title, url, price, buyer_protection, shipping_cost, seller_score, listed_at),
        )
        await db.commit()


async def alert_sent(item_id: str, source: str) -> bool:
    """Check if a notification has been sent for the given item."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM alerts WHERE item_id = ? AND source = ?", (item_id, source)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None


async def add_alert(item_id: str, source: str) -> None:
    """Record that an alert was sent for the given item."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO alerts (item_id, source) VALUES (?, ?)
            """,
            (item_id, source),
        )
        await db.commit()