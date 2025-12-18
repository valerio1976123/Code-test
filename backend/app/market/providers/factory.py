from __future__ import annotations

from app.core.config import settings
from app.market.providers.base import MarketDataProvider
from app.market.providers.mock import MockMarketDataProvider


def get_market_data_provider() -> MarketDataProvider:
    """
    Factory for the active market data provider.

    - dev: deterministic mock provider
    - prod: placeholder (swap in real API providers later)
    """
    if settings.is_dev:
        return MockMarketDataProvider()

    # PROD mode: prepared for real providers. For now, keep mock to avoid breaking startup.
    # Replace this with Alpha Vantage / Yahoo Finance implementations later.
    return MockMarketDataProvider()

