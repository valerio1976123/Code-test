from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class StockBase(BaseModel):
    symbol: str
    name: str = ""
    exchange: str = ""
    country: str = ""


class StockCreate(StockBase):
    pass


class StockOut(StockBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class IndexBase(BaseModel):
    symbol: str
    name: str = ""
    country: str = ""


class IndexCreate(IndexBase):
    pass


class IndexOut(IndexBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CountryMacroOut(BaseModel):
    country: str
    as_of_date: date
    gdp_growth: float | None = None
    inflation: float | None = None
    interest_rate: float | None = None
    unemployment: float | None = None
    sentiment_index: float | None = None

    class Config:
        from_attributes = True


class PriceBarOut(BaseModel):
    instrument_type: str
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    class Config:
        from_attributes = True


class PredictionOut(BaseModel):
    target_type: str
    target_identifier: str
    timestamp_generated: datetime
    forecast_horizon: str
    predicted_direction: str
    predicted_return: float
    model_used: str
    confidence_score: float
    extra: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class WatchlistStockOut(BaseModel):
    id: int
    user_id: int
    stock: StockOut
    created_at: datetime

    class Config:
        from_attributes = True


class WatchlistIndexOut(BaseModel):
    id: int
    user_id: int
    index: IndexOut
    created_at: datetime

    class Config:
        from_attributes = True


class AlertRuleCreate(BaseModel):
    target_type: str
    target_identifier: str
    rule_type: str
    comparator: str = "gt"
    threshold: float = 0.0
    direction: str | None = None


class AlertRuleOut(AlertRuleCreate):
    id: int
    user_id: int
    is_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: int
    user_id: int
    target_type: str
    target_identifier: str
    triggered_at: datetime
    severity: str
    message: str
    is_read: bool

    class Config:
        from_attributes = True


class AlertMarkReadIn(BaseModel):
    is_read: bool = True


class WatchlistItemSummaryOut(BaseModel):
    target_type: str  # stock|index
    symbol: str
    name: str
    country: str
    last_price: float | None = None
    daily_change_pct: float | None = None
    latest_prediction: PredictionOut | None = None


class OverviewOut(BaseModel):
    watchlist_items: int
    bullish_predictions: int
    bearish_predictions: int
    unread_alerts: int

