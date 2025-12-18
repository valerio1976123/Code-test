from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol


@dataclass(frozen=True)
class PriceBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class MacroSnapshot:
    country: str
    as_of_date: date
    gdp_growth: float | None
    inflation: float | None
    interest_rate: float | None
    unemployment: float | None
    sentiment_index: float | None


@dataclass(frozen=True)
class StockDef:
    symbol: str
    name: str
    exchange: str
    country: str


@dataclass(frozen=True)
class IndexDef:
    symbol: str
    name: str
    country: str


class MarketDataProvider(Protocol):
    """Pluggable market data provider interface (mock now, real APIs later)."""

    def list_stocks(self) -> list[StockDef]: ...

    def list_indexes(self) -> list[IndexDef]: ...

    def list_countries(self) -> list[str]: ...

    def get_price_history(
        self,
        *,
        instrument_type: str,  # stock|index
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[PriceBar]: ...

    def get_macro_history(self, *, country: str, start: date, end: date) -> list[MacroSnapshot]: ...

