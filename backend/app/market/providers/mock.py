from __future__ import annotations

import math
import random
from datetime import date, datetime, timedelta, timezone

from app.market.providers.base import IndexDef, MacroSnapshot, MarketDataProvider, PriceBar, StockDef


class MockMarketDataProvider(MarketDataProvider):
    """
    Deterministic mock provider for development.

    Generates synthetic daily OHLCV series using a seeded RNG per symbol,
    plus macro series per country.
    """

    def list_stocks(self) -> list[StockDef]:
        return [
            StockDef(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", country="US"),
            StockDef(symbol="MSFT", name="Microsoft Corp.", exchange="NASDAQ", country="US"),
            StockDef(symbol="TSLA", name="Tesla Inc.", exchange="NASDAQ", country="US"),
            StockDef(symbol="ENI", name="Eni S.p.A.", exchange="MIL", country="IT"),
            StockDef(symbol="SAP", name="SAP SE", exchange="XETRA", country="DE"),
        ]

    def list_indexes(self) -> list[IndexDef]:
        return [
            IndexDef(symbol="SPX", name="S&P 500", country="US"),
            IndexDef(symbol="DAX", name="DAX", country="DE"),
            IndexDef(symbol="FTSEMIB", name="FTSE MIB", country="IT"),
        ]

    def list_countries(self) -> list[str]:
        return ["US", "DE", "IT"]

    def get_price_history(
        self,
        *,
        instrument_type: str,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[PriceBar]:
        start_utc = _as_utc(start)
        end_utc = _as_utc(end)
        if end_utc <= start_utc:
            return []

        # Align to daily bars at 00:00 UTC
        cur = datetime(start_utc.year, start_utc.month, start_utc.day, tzinfo=timezone.utc)
        end_day = datetime(end_utc.year, end_utc.month, end_utc.day, tzinfo=timezone.utc)

        rng = random.Random(_stable_seed(f"{instrument_type}:{symbol}"))
        base = _base_price(symbol, instrument_type)
        drift = 0.0003 if instrument_type == "index" else 0.0005
        vol = 0.012 if instrument_type == "index" else 0.02

        # Make the path depend on absolute day index so it is deterministic across calls.
        bars: list[PriceBar] = []
        # Pre-warm to the start date so "start" doesn't reset the path.
        pre_days = _days_since_epoch(cur)
        for _ in range(pre_days % 365):
            _ = rng.random()

        last_close = base
        while cur <= end_day:
            shock = rng.gauss(0.0, vol)
            ret = drift + shock
            close = max(0.5, last_close * (1.0 + ret))

            # Create OHLC with an intraday range related to vol.
            day_range = abs(rng.gauss(0.0, vol)) * last_close
            open_ = max(0.5, last_close * (1.0 + rng.gauss(0.0, vol / 3)))
            high = max(open_, close) + day_range * 0.6
            low = max(0.5, min(open_, close) - day_range * 0.6)

            # Volume: rough scale by price and a symbol factor.
            vol_base = 1_000_000 if instrument_type == "stock" else 50_000_000
            volume = max(0.0, vol_base * (0.8 + rng.random() * 0.6) * (1.0 + 0.2 * math.sin(_days_since_epoch(cur) / 7)))

            if cur >= start_utc and cur <= end_utc:
                bars.append(
                    PriceBar(
                        timestamp=cur.replace(tzinfo=None),
                        open=float(open_),
                        high=float(high),
                        low=float(low),
                        close=float(close),
                        volume=float(volume),
                    )
                )

            last_close = close
            cur += timedelta(days=1)

        return bars

    def get_macro_history(self, *, country: str, start: date, end: date) -> list[MacroSnapshot]:
        if end < start:
            return []
        rng = random.Random(_stable_seed(f"macro:{country}"))
        cur = date(start.year, start.month, start.day)
        out: list[MacroSnapshot] = []
        while cur <= end:
            t = (cur.toordinal() % 365) / 365.0
            # Simple smooth cycles + country offsets.
            offs = {"US": 0.0, "DE": -0.2, "IT": -0.4}.get(country.upper(), 0.0)
            gdp = 2.0 + offs + 0.8 * math.sin(2 * math.pi * t) + rng.gauss(0.0, 0.1)
            inflation = 2.2 + 0.4 * math.sin(2 * math.pi * (t + 0.25)) + rng.gauss(0.0, 0.1)
            rate = 3.0 + 0.8 * math.sin(2 * math.pi * (t + 0.5)) + rng.gauss(0.0, 0.05)
            unemp = 5.0 - offs + 0.5 * math.sin(2 * math.pi * (t + 0.75)) + rng.gauss(0.0, 0.1)
            sentiment = 50.0 + 5.0 * math.sin(2 * math.pi * t) + rng.gauss(0.0, 0.5)

            out.append(
                MacroSnapshot(
                    country=country.upper(),
                    as_of_date=cur,
                    gdp_growth=float(gdp),
                    inflation=float(inflation),
                    interest_rate=float(rate),
                    unemployment=float(unemp),
                    sentiment_index=float(sentiment),
                )
            )
            # daily macro for mock (cheap)
            cur = cur + timedelta(days=1)
        return out


def _stable_seed(s: str) -> int:
    # Deterministic 32-bit seed from string.
    h = 2166136261
    for ch in s.encode("utf-8"):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return int(h)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _days_since_epoch(dt: datetime) -> int:
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return int((_as_utc(dt) - epoch).days)


def _base_price(symbol: str, instrument_type: str) -> float:
    s = symbol.upper()
    if instrument_type == "index":
        return {"SPX": 4500.0, "DAX": 17500.0, "FTSEMIB": 30000.0}.get(s, 5000.0)
    return {"AAPL": 190.0, "MSFT": 420.0, "TSLA": 250.0, "ENI": 15.0, "SAP": 170.0}.get(s, 100.0)

