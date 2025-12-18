from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    exchange: Mapped[str] = mapped_column(String(50), default="")
    country: Mapped[str] = mapped_column(String(2), index=True, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MarketIndex(Base):
    __tablename__ = "market_indexes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    country: Mapped[str] = mapped_column(String(2), index=True, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CountryMacroData(Base):
    __tablename__ = "country_macro_data"
    __table_args__ = (UniqueConstraint("country", "as_of_date", name="uq_country_macro_country_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country: Mapped[str] = mapped_column(String(2), index=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)

    gdp_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    inflation: Mapped[float | None] = mapped_column(Float, nullable=True)
    interest_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    unemployment: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_index: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PriceHistory(Base):
    """
    Historical OHLCV for either stocks or indexes.

    instrument_type: "stock" | "index"
    """

    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("instrument_type", "symbol", "timestamp", name="uq_price_instr_symbol_ts"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_type: Mapped[str] = mapped_column(String(10), index=True)  # stock|index
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)

    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    """
    Stores latest and historical predictions for stocks, indexes, and countries.
    """

    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("target_type", "target_identifier", "timestamp_generated", "forecast_horizon", name="uq_pred_target_ts_horizon"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_type: Mapped[str] = mapped_column(String(10), index=True)  # stock|index|country
    target_identifier: Mapped[str] = mapped_column(String(32), index=True)  # symbol or country code
    timestamp_generated: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)

    forecast_horizon: Mapped[str] = mapped_column(String(10), default="1d")  # 1d|1w|1m
    predicted_direction: Mapped[str] = mapped_column(String(10))  # UP|DOWN|FLAT
    predicted_return: Mapped[float] = mapped_column(Float, default=0.0)
    model_used: Mapped[str] = mapped_column(String(100), default="rf_v1")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)

    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"
    __table_args__ = (UniqueConstraint("user_id", "stock_id", name="uq_watchlist_user_stock"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    stock_id: Mapped[int] = mapped_column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    stock: Mapped[Stock] = relationship("Stock")


class WatchlistIndex(Base):
    __tablename__ = "watchlist_indexes"
    __table_args__ = (UniqueConstraint("user_id", "index_id", name="uq_watchlist_user_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    index_id: Mapped[int] = mapped_column(Integer, ForeignKey("market_indexes.id", ondelete="CASCADE"), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    index: Mapped[MarketIndex] = relationship("MarketIndex")


class AlertRule(Base):
    """
    Simple alert rules evaluated on refresh/prediction updates.

    rule_type:
      - price_threshold
      - daily_change_pct
      - prediction_confidence

    comparator: "gt" | "lt"
    """

    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    target_type: Mapped[str] = mapped_column(String(10), index=True)  # stock|index|country
    target_identifier: Mapped[str] = mapped_column(String(32), index=True)

    rule_type: Mapped[str] = mapped_column(String(50), index=True)
    comparator: Mapped[str] = mapped_column(String(5), default="gt")
    threshold: Mapped[float] = mapped_column(Float, default=0.0)

    direction: Mapped[str | None] = mapped_column(String(10), nullable=True)  # for prediction_confidence: UP|DOWN|FLAT
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("user_id", "triggered_at", "target_type", "target_identifier", "message", name="uq_alert_dedupe"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    target_type: Mapped[str] = mapped_column(String(10), index=True)
    target_identifier: Mapped[str] = mapped_column(String(32), index=True)

    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    severity: Mapped[str] = mapped_column(String(10), default="info")  # info|warning|critical
    message: Mapped[str] = mapped_column(String(500))

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
