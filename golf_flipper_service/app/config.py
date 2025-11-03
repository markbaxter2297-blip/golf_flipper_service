"""
configuration module.
"""

from dataclasses import dataclass, field
from typing import List
from decouple import config as env


@dataclass
class Settings:
    # basics
    env: str = env("ENV", default="prod")
    port: int = env("PORT", cast=int, default=8080)
    db_path: str = env("DB_PATH", default="./data/app.db")

    # lists come from env as JSON; default to empty lists
    keywords: List[str] = field(default_factory=list)
    ebay_category_ids: List[str] = field(default_factory=list)

    # polling / thresholds
    profit_threshold_gbp: float = env("PROFIT_THRESHOLD_GBP", cast=float, default=12.0)
    poll_interval_seconds: int = env("POLL_INTERVAL_SECONDS", cast=int, default=300)

    # whatsapp
    whatsapp_access_token: str = env("WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = env("WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_to_msisdn: str = env("WHATSAPP_TO_MSISDN", default="")

    # ebay
    ebay_app_id: str = env("EBAY_APP_ID", default="")
    ebay_cert_id: str = env("EBAY_CERT_ID", default="")
    ebay_redirect_uri: str = env("EBAY_REDIRECT_URI", default="")
    ebay_market: str = env("EBAY_MARKET", default="EBAY_GB")

    # vinted
    vinted_enabled: bool = env("VINTED_ENABLED", cast=bool, default=False)
    vinted_base_url: str = env("VINTED_BASE_URL", default="https://www.vinted.co.uk")
    vinted_cookie: str = env("VINTED_COOKIE", default="")

    # logging
    log_level: str = env("LOG_LEVEL", default="INFO")


settings = Settings()
