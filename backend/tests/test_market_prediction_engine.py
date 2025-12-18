from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.market.prediction.prediction_engine import predict_country_outlook, predict_symbol
from app.models.market import CountryMacroData, MarketIndex, PriceHistory


def _mk_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def test_predict_symbol_returns_result() -> None:
    db = _mk_session()
    now = datetime(2025, 1, 1)
    # insert 200 daily bars with mild upward drift
    close = 100.0
    for i in range(220):
        ts = now + timedelta(days=i)
        close = close * (1.0 + 0.0005)
        db.add(
            PriceHistory(
                instrument_type="stock",
                symbol="AAPL",
                timestamp=ts,
                open=close * 0.995,
                high=close * 1.01,
                low=close * 0.99,
                close=close,
                volume=1_000_000 + i * 1000,
            )
        )
    db.commit()

    res = predict_symbol(db, instrument_type="stock", symbol="AAPL", horizon_days=1)
    assert res is not None
    assert res.target_identifier == "AAPL"
    assert res.predicted_direction in {"UP", "DOWN", "FLAT"}
    assert 0.0 <= res.confidence_score <= 1.0


def test_predict_country_outlook_returns_result() -> None:
    db = _mk_session()
    db.add(MarketIndex(symbol="SPX", name="S&P 500", country="US"))
    db.commit()

    now = datetime(2025, 1, 1)
    close = 4500.0
    for i in range(120):
        ts = now + timedelta(days=i)
        close = close * (1.0 + 0.0003)
        db.add(
            PriceHistory(
                instrument_type="index",
                symbol="SPX",
                timestamp=ts,
                open=close * 0.995,
                high=close * 1.01,
                low=close * 0.99,
                close=close,
                volume=50_000_000,
            )
        )
    db.add(
        CountryMacroData(
            country="US",
            as_of_date=date(2025, 4, 1),
            gdp_growth=2.2,
            inflation=2.3,
            interest_rate=3.5,
            unemployment=4.8,
            sentiment_index=52.0,
        )
    )
    db.commit()

    res = predict_country_outlook(db, country="US")
    assert res is not None
    assert res.target_type == "country"
    assert res.target_identifier == "US"
    assert res.extra and "label" in res.extra

