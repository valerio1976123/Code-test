from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.market.deps import get_market_user
from app.market.jobs import market_refresh_data_job, market_run_predictions_job
from app.market.prediction.prediction_engine import predict_country_outlook, predict_symbol, store_prediction
from app.market.providers.factory import get_market_data_provider
from app.market.services.alerts import evaluate_alerts_for_user
from app.market.services.data_refresh import ensure_default_universe, ensure_demo_watchlists
from app.models.market import (
    Alert,
    AlertRule,
    CountryMacroData,
    MarketIndex,
    Prediction,
    PriceHistory,
    Stock,
    WatchlistIndex,
    WatchlistStock,
)
from app.schemas.market import (
    AlertMarkReadIn,
    AlertOut,
    AlertRuleCreate,
    AlertRuleOut,
    CountryMacroOut,
    IndexOut,
    OverviewOut,
    PredictionOut,
    PriceBarOut,
    StockOut,
    WatchlistItemSummaryOut,
    WatchlistIndexOut,
    WatchlistStockOut,
)

router = APIRouter()


def _latest_prediction(db: Session, *, target_type: str, target_identifier: str) -> Prediction | None:
    return (
        db.execute(
            select(Prediction)
            .where(and_(Prediction.target_type == target_type, Prediction.target_identifier == target_identifier))
            .order_by(desc(Prediction.timestamp_generated))
            .limit(1)
        )
        .scalars()
        .first()
    )


def _latest_price_and_change(db: Session, *, instrument_type: str, symbol: str) -> tuple[float | None, float | None]:
    rows = (
        db.execute(
            select(PriceHistory)
            .where(and_(PriceHistory.instrument_type == instrument_type, PriceHistory.symbol == symbol))
            .order_by(desc(PriceHistory.timestamp))
            .limit(2)
        )
        .scalars()
        .all()
    )
    if not rows:
        return None, None
    last = float(rows[0].close)
    if len(rows) < 2:
        return last, None
    prev = float(rows[1].close)
    if prev == 0:
        return last, None
    return last, (last / prev - 1.0) * 100.0


@router.get("/overview", response_model=OverviewOut)
def overview(user=Depends(get_market_user), db: Session = Depends(get_db)) -> dict[str, int]:
    ensure_demo_watchlists(db, user_id=user.id)

    wl_stocks = db.execute(select(WatchlistStock).where(WatchlistStock.user_id == user.id)).scalars().all()
    wl_indexes = db.execute(select(WatchlistIndex).where(WatchlistIndex.user_id == user.id)).scalars().all()
    items = len(wl_stocks) + len(wl_indexes)

    bullish = 0
    bearish = 0
    for wl in wl_stocks:
        p = _latest_prediction(db, target_type="stock", target_identifier=wl.stock.symbol)
        if not p:
            continue
        if p.predicted_direction == "UP":
            bullish += 1
        elif p.predicted_direction == "DOWN":
            bearish += 1
    for wl in wl_indexes:
        p = _latest_prediction(db, target_type="index", target_identifier=wl.index.symbol)
        if not p:
            continue
        if p.predicted_direction == "UP":
            bullish += 1
        elif p.predicted_direction == "DOWN":
            bearish += 1

    unread = (
        db.execute(select(func.count(Alert.id)).where(and_(Alert.user_id == user.id, Alert.is_read.is_(False))))
        .scalar_one()
        or 0
    )
    return {
        "watchlist_items": int(items),
        "bullish_predictions": int(bullish),
        "bearish_predictions": int(bearish),
        "unread_alerts": int(unread),
    }


@router.get("/watchlist/summary", response_model=list[WatchlistItemSummaryOut])
def watchlist_summary(user=Depends(get_market_user), db: Session = Depends(get_db)) -> list[WatchlistItemSummaryOut]:
    ensure_demo_watchlists(db, user_id=user.id)
    out: list[WatchlistItemSummaryOut] = []

    wl_stocks = db.execute(select(WatchlistStock).where(WatchlistStock.user_id == user.id)).scalars().all()
    for wl in wl_stocks:
        sym = wl.stock.symbol
        last, chg = _latest_price_and_change(db, instrument_type="stock", symbol=sym)
        pred = _latest_prediction(db, target_type="stock", target_identifier=sym)
        out.append(
            WatchlistItemSummaryOut(
                target_type="stock",
                symbol=sym,
                name=wl.stock.name,
                country=wl.stock.country,
                last_price=last,
                daily_change_pct=chg,
                latest_prediction=PredictionOut.model_validate(pred) if pred else None,  # type: ignore[attr-defined]
            )
        )

    wl_indexes = db.execute(select(WatchlistIndex).where(WatchlistIndex.user_id == user.id)).scalars().all()
    for wl in wl_indexes:
        sym = wl.index.symbol
        last, chg = _latest_price_and_change(db, instrument_type="index", symbol=sym)
        pred = _latest_prediction(db, target_type="index", target_identifier=sym)
        out.append(
            WatchlistItemSummaryOut(
                target_type="index",
                symbol=sym,
                name=wl.index.name,
                country=wl.index.country,
                last_price=last,
                daily_change_pct=chg,
                latest_prediction=PredictionOut.model_validate(pred) if pred else None,  # type: ignore[attr-defined]
            )
        )
    return out


@router.get("/stocks", response_model=list[StockOut])
def list_stocks(db: Session = Depends(get_db)) -> list[Stock]:
    provider = get_market_data_provider()
    ensure_default_universe(db, provider)
    return db.execute(select(Stock).order_by(Stock.symbol.asc())).scalars().all()


@router.get("/stocks/{symbol}", response_model=StockOut)
def get_stock(symbol: str, db: Session = Depends(get_db)) -> Stock:
    stock = db.execute(select(Stock).where(Stock.symbol == symbol.upper())).scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@router.get("/indexes", response_model=list[IndexOut])
def list_indexes(db: Session = Depends(get_db)) -> list[MarketIndex]:
    provider = get_market_data_provider()
    ensure_default_universe(db, provider)
    return db.execute(select(MarketIndex).order_by(MarketIndex.symbol.asc())).scalars().all()


@router.get("/indexes/{symbol}", response_model=IndexOut)
def get_index(symbol: str, db: Session = Depends(get_db)) -> MarketIndex:
    idx = db.execute(select(MarketIndex).where(MarketIndex.symbol == symbol.upper())).scalar_one_or_none()
    if not idx:
        raise HTTPException(status_code=404, detail="Index not found")
    return idx


@router.get("/countries", response_model=list[str])
def list_countries(db: Session = Depends(get_db)) -> list[str]:
    # from macro table if present, otherwise provider list
    existing = db.execute(select(CountryMacroData.country).distinct()).scalars().all()
    if existing:
        return sorted({c.upper() for c in existing})
    return get_market_data_provider().list_countries()


@router.get("/countries/{country_code}/macro", response_model=list[CountryMacroOut])
def country_macro_history(
    country_code: str,
    days: int = Query(default=120, ge=7, le=3650),
    db: Session = Depends(get_db),
) -> list[CountryMacroData]:
    country = country_code.upper()
    start = date.today() - timedelta(days=days)
    return (
        db.execute(
            select(CountryMacroData)
            .where(and_(CountryMacroData.country == country, CountryMacroData.as_of_date >= start))
            .order_by(CountryMacroData.as_of_date.asc())
        )
        .scalars()
        .all()
    )


@router.get("/watchlist/stocks", response_model=list[WatchlistStockOut])
def get_watchlist_stocks(user=Depends(get_market_user), db: Session = Depends(get_db)) -> list[WatchlistStock]:
    ensure_demo_watchlists(db, user_id=user.id)
    return (
        db.execute(select(WatchlistStock).where(WatchlistStock.user_id == user.id).order_by(WatchlistStock.id.asc()))
        .scalars()
        .all()
    )


@router.post("/watchlist/stocks/{symbol}", response_model=WatchlistStockOut)
def add_watchlist_stock(symbol: str, user=Depends(get_market_user), db: Session = Depends(get_db)) -> WatchlistStock:
    sym = symbol.upper()
    stock = db.execute(select(Stock).where(Stock.symbol == sym)).scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    existing = db.execute(
        select(WatchlistStock).where(and_(WatchlistStock.user_id == user.id, WatchlistStock.stock_id == stock.id))
    ).scalar_one_or_none()
    if existing:
        return existing
    wl = WatchlistStock(user_id=user.id, stock_id=stock.id)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return wl


@router.delete("/watchlist/stocks/{symbol}")
def remove_watchlist_stock(symbol: str, user=Depends(get_market_user), db: Session = Depends(get_db)) -> dict[str, bool]:
    sym = symbol.upper()
    stock = db.execute(select(Stock).where(Stock.symbol == sym)).scalar_one_or_none()
    if not stock:
        return {"removed": False}
    wl = db.execute(
        select(WatchlistStock).where(and_(WatchlistStock.user_id == user.id, WatchlistStock.stock_id == stock.id))
    ).scalar_one_or_none()
    if not wl:
        return {"removed": False}
    db.delete(wl)
    db.commit()
    return {"removed": True}


@router.get("/watchlist/countries", response_model=list[WatchlistIndexOut])
def get_watchlist_countries(user=Depends(get_market_user), db: Session = Depends(get_db)) -> list[WatchlistIndex]:
    """
    Country/Index watchlist. Implemented as a watchlist of main indexes.
    """
    ensure_demo_watchlists(db, user_id=user.id)
    return (
        db.execute(select(WatchlistIndex).where(WatchlistIndex.user_id == user.id).order_by(WatchlistIndex.id.asc()))
        .scalars()
        .all()
    )


@router.post("/watchlist/countries/{index_symbol}", response_model=WatchlistIndexOut)
def add_watchlist_country(index_symbol: str, user=Depends(get_market_user), db: Session = Depends(get_db)) -> WatchlistIndex:
    sym = index_symbol.upper()
    idx = db.execute(select(MarketIndex).where(MarketIndex.symbol == sym)).scalar_one_or_none()
    if not idx:
        raise HTTPException(status_code=404, detail="Index not found")
    existing = db.execute(
        select(WatchlistIndex).where(and_(WatchlistIndex.user_id == user.id, WatchlistIndex.index_id == idx.id))
    ).scalar_one_or_none()
    if existing:
        return existing
    wl = WatchlistIndex(user_id=user.id, index_id=idx.id)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return wl


@router.delete("/watchlist/countries/{index_symbol}")
def remove_watchlist_country(index_symbol: str, user=Depends(get_market_user), db: Session = Depends(get_db)) -> dict[str, bool]:
    sym = index_symbol.upper()
    idx = db.execute(select(MarketIndex).where(MarketIndex.symbol == sym)).scalar_one_or_none()
    if not idx:
        return {"removed": False}
    wl = db.execute(
        select(WatchlistIndex).where(and_(WatchlistIndex.user_id == user.id, WatchlistIndex.index_id == idx.id))
    ).scalar_one_or_none()
    if not wl:
        return {"removed": False}
    db.delete(wl)
    db.commit()
    return {"removed": True}


@router.get("/prices/{symbol}", response_model=list[PriceBarOut])
def get_prices(
    symbol: str,
    instrument_type: str = Query(default="stock", pattern="^(stock|index)$"),
    days: int = Query(default=180, ge=7, le=3650),
    db: Session = Depends(get_db),
) -> list[PriceHistory]:
    sym = symbol.upper()
    start = datetime.utcnow() - timedelta(days=days)
    return (
        db.execute(
            select(PriceHistory)
            .where(and_(PriceHistory.instrument_type == instrument_type, PriceHistory.symbol == sym, PriceHistory.timestamp >= start))
            .order_by(PriceHistory.timestamp.asc())
        )
        .scalars()
        .all()
    )


@router.get("/predictions/{symbol}", response_model=list[PredictionOut])
def prediction_history(
    symbol: str,
    target_type: str = Query(default="stock", pattern="^(stock|index)$"),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Prediction]:
    sym = symbol.upper()
    return (
        db.execute(
            select(Prediction)
            .where(and_(Prediction.target_type == target_type, Prediction.target_identifier == sym))
            .order_by(desc(Prediction.timestamp_generated))
            .limit(limit)
        )
        .scalars()
        .all()
    )


@router.get("/predictions/country/{country_code}", response_model=list[PredictionOut])
def country_prediction_history(
    country_code: str,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Prediction]:
    c = country_code.upper()
    return (
        db.execute(
            select(Prediction)
            .where(and_(Prediction.target_type == "country", Prediction.target_identifier == c))
            .order_by(desc(Prediction.timestamp_generated))
            .limit(limit)
        )
        .scalars()
        .all()
    )


@router.post("/admin/refresh-data")
def admin_refresh_data() -> dict[str, int]:
    # trigger immediate refresh
    return market_refresh_data_job()


@router.post("/admin/retrain")
def admin_retrain() -> dict[str, int]:
    # In this MVP, "retrain" is equivalent to running predictions now.
    return market_run_predictions_job()


@router.post("/admin/predict/{symbol}", response_model=PredictionOut)
def admin_predict_symbol(
    symbol: str,
    target_type: str = Query(default="stock", pattern="^(stock|index)$"),
    db: Session = Depends(get_db),
) -> Prediction:
    sym = symbol.upper()
    res = predict_symbol(db, instrument_type=target_type, symbol=sym, horizon_days=1)
    if not res:
        raise HTTPException(status_code=400, detail="Not enough data to predict yet")
    return store_prediction(db, res)


@router.post("/admin/predict-country/{country_code}", response_model=PredictionOut)
def admin_predict_country(country_code: str, db: Session = Depends(get_db)) -> Prediction:
    c = country_code.upper()
    res = predict_country_outlook(db, country=c)
    if not res:
        raise HTTPException(status_code=400, detail="Not enough data to predict country yet")
    return store_prediction(db, res)


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    user=Depends(get_market_user),
    is_read: bool | None = Query(default=None),
    target_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Alert]:
    q = select(Alert).where(Alert.user_id == user.id)
    if is_read is not None:
        q = q.where(Alert.is_read.is_(is_read))
    if target_type:
        q = q.where(Alert.target_type == target_type)
    return db.execute(q.order_by(desc(Alert.triggered_at)).limit(limit)).scalars().all()


@router.patch("/alerts/{alert_id}", response_model=AlertOut)
def mark_alert_read(
    alert_id: int,
    body: AlertMarkReadIn,
    user=Depends(get_market_user),
    db: Session = Depends(get_db),
) -> Alert:
    a = db.get(Alert, alert_id)
    if not a or a.user_id != user.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    a.is_read = bool(body.is_read)
    db.commit()
    db.refresh(a)
    return a


@router.post("/alert-rules", response_model=AlertRuleOut)
def create_alert_rule(
    body: AlertRuleCreate,
    user=Depends(get_market_user),
    db: Session = Depends(get_db),
) -> AlertRule:
    rule = AlertRule(
        user_id=user.id,
        target_type=body.target_type,
        target_identifier=body.target_identifier.upper(),
        rule_type=body.rule_type,
        comparator=body.comparator,
        threshold=body.threshold,
        direction=body.direction,
        is_enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/admin/evaluate-alerts")
def admin_eval_alerts(user=Depends(get_market_user), db: Session = Depends(get_db)) -> dict[str, int]:
    created = evaluate_alerts_for_user(db, user_id=user.id)
    return {"alerts_created": int(created)}

