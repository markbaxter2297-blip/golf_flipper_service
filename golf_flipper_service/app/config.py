"""
Configuration module.

Reads environment variables from a `.env` file or system environment using python-decouple.
Provides a Pydantic model for validated configuration values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from dataclasses import dataclass, field

from decouple import config as decouple_config


def _str_to_list(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    env: str = decouple_config("ENV", default="prod")
    port: int = decouple_config("PORT", cast=int, default=8080)
    db_path: str = decouple_config("DB_PATH", default="./data/app.db")

   keywords: List[str] = field(default_factory=list)
    ebay_category_ids: List[str] = field(default_factory=list)
    profit_threshold_gbp: float = decouple_config("PROFIT_THRESHOLD_GBP", cast=float, default=12.0)
    poll_interval_seconds: int = decouple_config("POLL_INTERVAL_SECONDS", cast=int, default=300)

    whatsapp_access_token: str = decouple_config("WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = decouple_config("WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_to_msisdn: str = decouple_config("WHATSAPP_TO_MSISDN")

    ebay_app_id: str = decouple_config("EBAY_APP_ID")
    ebay_cert_id: str = decouple_config("EBAY_CERT_ID")
    ebay_redirect_uri: str = decouple_config("EBAY_REDIRECT_URI")
    ebay_market: str = decouple_config("EBAY_MARKET", default="EBAY_GB")

    vinted_enabled: bool = decouple_config("VINTED_ENABLED", cast=bool, default=True)
    vinted_base_url: str = decouple_config("VINTED_BASE_URL", default="https://www.vinted.co.uk")
    vinted_cookie: str = decouple_config("VINTED_COOKIE", default="")

    log_level: str = decouple_config("LOG_LEVEL", default="INFO")

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls()


# Global singleton settings instance
settings: Settings = Settings.load()
