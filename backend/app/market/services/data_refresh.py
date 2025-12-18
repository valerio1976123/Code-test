from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.market.providers.base import MarketDataProvider
from app.models.market import CountryMacroData, MarketIndex, PriceHistory, Stock, WatchlistIndex, WatchlistStock


@dataclass(frozen=True)
class RefreshResult:
    stocks_upserted: int = 0
    indexes_upserted: int = 0
    price_rows_inserted: int = 0
    macro_rows_inserted: int = 0


def ensure_default_universe(db: Session, provider: MarketDataProvider) -> RefreshResult:
    stocks_up = 0
    for s in provider.list_stocks():
        existing = db.execute(select(Stock).where(Stock.symbol == s.symbol)).scalar_one_or_none()
        if existing:
            # keep names fresh
            changed = False
            if existing.name != s.name:
                existing.name = s.name
                changed = True
            if existing.exchange != s.exchange:
                existing.exchange = s.exchange
                changed = True
            if existing.country != s.country:
                existing.country = s.country
                changed = True
            if changed:
                stocks_up += 1
        else:
            db.add(Stock(symbol=s.symbol, name=s.name, exchange=s.exchange, country=s.country))
            stocks_up += 1

    idx_up = 0
    for i in provider.list_indexes():
        existing = db.execute(select(MarketIndex).where(MarketIndex.symbol == i.symbol)).scalar_one_or_none()
        if existing:
            changed = False
            if existing.name != i.name:
                existing.name = i.name
                changed = True
            if existing.country != i.country:
                existing.country = i.country
                changed = True
            if changed:
                idx_up += 1
        else:
            db.add(MarketIndex(symbol=i.symbol, name=i.name, country=i.country))
            idx_up += 1

    db.commit()
    return RefreshResult(stocks_upserted=stocks_up, indexes_upserted=idx_up)


def ensure_demo_watchlists(db: Session, *, user_id: int) -> None:
    """
    Keep a small default watchlist so the UI has something to show in dev.
    """
    # If already has items, leave as-is.
    has_any = db.execute(select(func.count(WatchlistStock.id)).where(WatchlistStock.user_id == user_id)).scalar_one()
    has_any2 = db.execute(select(func.count(WatchlistIndex.id)).where(WatchlistIndex.user_id == user_id)).scalar_one()
    if (has_any or 0) > 0 or (has_any2 or 0) > 0:
        return

    stocks = db.execute(select(Stock).order_by(Stock.symbol.asc()).limit(3)).scalars().all()
    indexes = db.execute(select(MarketIndex).order_by(MarketIndex.symbol.asc()).limit(3)).scalars().all()
    for s in stocks:
        db.add(WatchlistStock(user_id=user_id, stock_id=s.id))
    for i in indexes:
        db.add(WatchlistIndex(user_id=user_id, index_id=i.id))
    db.commit()


def refresh_price_data(
    db: Session,
    provider: MarketDataProvider,
    *,
    instrument_type: str,
    symbol: str,
    lookback_days: int = 420,
) -> int:
    last_ts = db.execute(
        select(func.max(PriceHistory.timestamp)).where(
            and_(PriceHistory.instrument_type == instrument_type, PriceHistory.symbol == symbol)
        )
    ).scalar_one()

    if last_ts:
        start = last_ts + timedelta(days=1)
    else:
        start = datetime.utcnow() - timedelta(days=lookback_days)
    end = datetime.utcnow()

    bars = provider.get_price_history(instrument_type=instrument_type, symbol=symbol, start=start, end=end)
    inserted = 0
    for b in bars:
        # Unique constraint guards duplicates; we also skip if already exists.
        exists = db.execute(
            select(PriceHistory.id).where(
                and_(
                    PriceHistory.instrument_type == instrument_type,
                    PriceHistory.symbol == symbol,
                    PriceHistory.timestamp == b.timestamp,
                )
            )
        ).scalar_one_or_none()
        if exists:
            continue
        db.add(
            PriceHistory(
                instrument_type=instrument_type,
                symbol=symbol,
                timestamp=b.timestamp,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
            )
        )
        inserted += 1

    db.commit()
    return inserted


def refresh_all_prices(db: Session, provider: MarketDataProvider) -> int:
    inserted = 0
    for s in db.execute(select(Stock)).scalars().all():
        inserted += refresh_price_data(db, provider, instrument_type="stock", symbol=s.symbol)
    for i in db.execute(select(MarketIndex)).scalars().all():
        inserted += refresh_price_data(db, provider, instrument_type="index", symbol=i.symbol)
    return inserted


def refresh_macro_data(db: Session, provider: MarketDataProvider, *, country: str, lookback_days: int = 365) -> int:
    last_date = db.execute(
        select(func.max(CountryMacroData.as_of_date)).where(CountryMacroData.country == country)
    ).scalar_one()

    if last_date:
        start = last_date + timedelta(days=1)
    else:
        start = date.today() - timedelta(days=lookback_days)
    end = date.today()

    snapshots = provider.get_macro_history(country=country, start=start, end=end)
    inserted = 0
    for s in snapshots:
        exists = db.execute(
            select(CountryMacroData.id).where(
                and_(CountryMacroData.country == s.country, CountryMacroData.as_of_date == s.as_of_date)
            )
        ).scalar_one_or_none()
        if exists:
            continue
        db.add(
            CountryMacroData(
                country=s.country,
                as_of_date=s.as_of_date,
                gdp_growth=s.gdp_growth,
                inflation=s.inflation,
                interest_rate=s.interest_rate,
                unemployment=s.unemployment,
                sentiment_index=s.sentiment_index,
            )
        )
        inserted += 1
    db.commit()
    return inserted


def refresh_all_macro(db: Session, provider: MarketDataProvider) -> int:
    inserted = 0
    for c in provider.list_countries():
        inserted += refresh_macro_data(db, provider, country=c)
    return inserted

