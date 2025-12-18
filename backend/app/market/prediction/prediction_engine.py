from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.market.prediction.feature_engineering import make_supervised
from app.models.market import CountryMacroData, MarketIndex, Prediction, PriceHistory


@dataclass(frozen=True)
class PredictionResult:
    target_type: str
    target_identifier: str
    forecast_horizon: str
    predicted_direction: str
    predicted_return: float
    confidence_score: float
    model_used: str
    extra: dict[str, Any] | None = None


def _dir_from_label(label: int) -> str:
    if label > 0:
        return "UP"
    if label < 0:
        return "DOWN"
    return "FLAT"


def predict_symbol(
    db: Session,
    *,
    instrument_type: str,  # stock|index
    symbol: str,
    horizon_days: int = 1,
) -> PredictionResult | None:
    rows = (
        db.execute(
            select(PriceHistory)
            .where(and_(PriceHistory.instrument_type == instrument_type, PriceHistory.symbol == symbol))
            .order_by(PriceHistory.timestamp.asc())
        )
        .scalars()
        .all()
    )
    if len(rows) < 120:
        return None

    df = pd.DataFrame(
        [
            {
                "timestamp": r.timestamp,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in rows
        ]
    )
    ds = make_supervised(df, horizon_days=horizon_days)
    if ds.X.shape[0] < 50:
        return None

    # Simple split: train on all but last row; predict on last row.
    X_train = ds.X.iloc[:-1]
    y_train = ds.y_cls.iloc[:-1]
    y_ret_train = ds.y_ret.iloc[:-1]

    X_pred = ds.X.iloc[[-1]]

    clf = RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced", n_jobs=1)
    clf.fit(X_train, y_train)

    reg = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=1)
    reg.fit(X_train, y_ret_train)

    proba = clf.predict_proba(X_pred)[0]
    classes = list(clf.classes_)
    best_idx = int(proba.argmax())
    best_label = int(classes[best_idx])
    confidence = float(proba[best_idx])

    pred_ret = float(reg.predict(X_pred)[0])

    fi = []
    try:
        for name, val in sorted(zip(ds.X.columns, clf.feature_importances_), key=lambda t: t[1], reverse=True)[:8]:
            fi.append({"feature": str(name), "importance": float(val)})
    except Exception:
        fi = []

    return PredictionResult(
        target_type=instrument_type,
        target_identifier=symbol,
        forecast_horizon=f"{horizon_days}d",
        predicted_direction=_dir_from_label(best_label),
        predicted_return=pred_ret * 100.0,  # store as %
        confidence_score=confidence,
        model_used="rf_v1",
        extra={"top_features": fi},
    )


def store_prediction(db: Session, pred: PredictionResult) -> Prediction:
    obj = Prediction(
        target_type=pred.target_type,
        target_identifier=pred.target_identifier,
        timestamp_generated=datetime.utcnow(),
        forecast_horizon=pred.forecast_horizon,
        predicted_direction=pred.predicted_direction,
        predicted_return=pred.predicted_return,
        model_used=pred.model_used,
        confidence_score=pred.confidence_score,
        extra=pred.extra,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def predict_country_outlook(db: Session, *, country: str) -> PredictionResult | None:
    """
    Simple country outlook score in [-1, +1] based on:
    - index recent returns
    - macro snapshot (inflation, rates, unemployment, sentiment)
    """
    country = country.upper()

    # Pick the "main index" for the country (first by symbol).
    idx = db.execute(select(MarketIndex).where(MarketIndex.country == country).order_by(MarketIndex.symbol.asc())).scalar_one_or_none()
    if not idx:
        return None

    prices = (
        db.execute(
            select(PriceHistory)
            .where(and_(PriceHistory.instrument_type == "index", PriceHistory.symbol == idx.symbol))
            .order_by(PriceHistory.timestamp.asc())
        )
        .scalars()
        .all()
    )
    if len(prices) < 60:
        return None

    closes = pd.Series([p.close for p in prices], dtype=float)
    ret_20 = float(closes.iloc[-1] / closes.iloc[-21] - 1.0) if len(closes) >= 21 else 0.0
    ret_60 = float(closes.iloc[-1] / closes.iloc[-61] - 1.0) if len(closes) >= 61 else 0.0

    macro = (
        db.execute(select(CountryMacroData).where(CountryMacroData.country == country).order_by(CountryMacroData.as_of_date.desc()))
        .scalars()
        .first()
    )
    if not macro:
        return None

    # Heuristic scoring
    infl = float(macro.inflation or 0.0)
    rate = float(macro.interest_rate or 0.0)
    unemp = float(macro.unemployment or 0.0)
    sent = float(macro.sentiment_index or 50.0)

    score = 0.0
    score += 0.6 * ret_20
    score += 0.4 * ret_60
    score += 0.002 * (sent - 50.0)
    score -= 0.02 * max(0.0, infl - 2.0)
    score -= 0.01 * max(0.0, rate - 3.0)
    score -= 0.01 * max(0.0, unemp - 5.0)

    score = max(-1.0, min(1.0, score))
    if score > 0.15:
        label = "BULLISH"
        direction = "UP"
    elif score < -0.15:
        label = "BEARISH"
        direction = "DOWN"
    else:
        label = "NEUTRAL"
        direction = "FLAT"

    return PredictionResult(
        target_type="country",
        target_identifier=country,
        forecast_horizon="1m",
        predicted_direction=direction,
        predicted_return=score * 100.0,
        confidence_score=float(min(1.0, abs(score) + 0.25)),
        model_used="heuristic_country_v1",
        extra={"score": score, "label": label, "main_index": idx.symbol},
    )

