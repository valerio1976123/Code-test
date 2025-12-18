from __future__ import annotations

from datetime import datetime, timedelta

from app.market.providers.mock import MockMarketDataProvider


def test_mock_provider_deterministic() -> None:
    p = MockMarketDataProvider()
    start = datetime.utcnow() - timedelta(days=30)
    end = datetime.utcnow()

    a = p.get_price_history(instrument_type="stock", symbol="AAPL", start=start, end=end)
    b = p.get_price_history(instrument_type="stock", symbol="AAPL", start=start, end=end)

    assert len(a) == len(b)
    if a:
        assert a[0].open == b[0].open
        assert a[-1].close == b[-1].close

