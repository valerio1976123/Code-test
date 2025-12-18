from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.market.prediction.prediction_engine import predict_country_outlook, predict_symbol, store_prediction
from app.market.providers.factory import get_market_data_provider
from app.market.services.alerts import evaluate_alerts_for_user
from app.market.services.data_refresh import ensure_default_universe, ensure_demo_watchlists, refresh_all_macro, refresh_all_prices
from app.models.market import WatchlistIndex, WatchlistStock
from app.models.user import User
from app.security.passwords import hash_password


def _ensure_demo_user_id(db) -> int:
    user = db.execute(select(User).where(User.username == "demo")).scalar_one_or_none()
    if user:
        return int(user.id)
    user = User(username="demo", password_hash=hash_password("demo"), is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return int(user.id)


def market_refresh_data_job() -> dict[str, int]:
    """
    Refresh universe + prices + macro using the configured provider.
    Intended to run periodically via APScheduler.
    """
    provider = get_market_data_provider()
    with SessionLocal() as db:
        ensure_default_universe(db, provider)
        demo_id = _ensure_demo_user_id(db)
        ensure_demo_watchlists(db, user_id=demo_id)

        prices = refresh_all_prices(db, provider)
        macro = refresh_all_macro(db, provider)
        return {"prices_inserted": int(prices), "macro_inserted": int(macro)}


def market_run_predictions_job() -> dict[str, int]:
    """
    Generate predictions for watchlist items and country outlook.
    """
    created = 0
    with SessionLocal() as db:
        demo_id = _ensure_demo_user_id(db)
        ensure_demo_watchlists(db, user_id=demo_id)

        wl_stocks = (
            db.execute(select(WatchlistStock).where(WatchlistStock.user_id == demo_id)).scalars().all()
        )
        for wl in wl_stocks:
            sym = wl.stock.symbol
            res = predict_symbol(db, instrument_type="stock", symbol=sym, horizon_days=1)
            if res:
                store_prediction(db, res)
                created += 1

        wl_indexes = (
            db.execute(select(WatchlistIndex).where(WatchlistIndex.user_id == demo_id)).scalars().all()
        )
        countries = set()
        for wl in wl_indexes:
            sym = wl.index.symbol
            countries.add(wl.index.country)
            res = predict_symbol(db, instrument_type="index", symbol=sym, horizon_days=1)
            if res:
                store_prediction(db, res)
                created += 1

        for c in sorted(countries):
            cres = predict_country_outlook(db, country=c)
            if cres:
                store_prediction(db, cres)
                created += 1

    return {"predictions_created": int(created), "timestamp": int(datetime.utcnow().timestamp())}


def market_evaluate_alerts_job() -> dict[str, int]:
    with SessionLocal() as db:
        demo_id = _ensure_demo_user_id(db)
        created = evaluate_alerts_for_user(db, user_id=demo_id)
        return {"alerts_created": int(created)}

