from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.models.market import Alert, AlertRule, Prediction, PriceHistory


def _cmp(val: float, comparator: str, threshold: float) -> bool:
    if comparator == "lt":
        return val < threshold
    return val > threshold


def evaluate_alerts_for_user(db: Session, *, user_id: int) -> int:
    """
    Evaluate enabled rules and store triggered alerts.
    Returns number of newly created alerts.
    """
    rules = (
        db.execute(select(AlertRule).where(and_(AlertRule.user_id == user_id, AlertRule.is_enabled.is_(True))))
        .scalars()
        .all()
    )
    created = 0
    now = datetime.utcnow()

    for r in rules:
        if r.rule_type == "price_threshold":
            ph = (
                db.execute(
                    select(PriceHistory)
                    .where(and_(PriceHistory.symbol == r.target_identifier))
                    .order_by(desc(PriceHistory.timestamp))
                    .limit(1)
                )
                .scalars()
                .first()
            )
            if not ph:
                continue
            if _cmp(float(ph.close), r.comparator, float(r.threshold)):
                created += _create_alert(
                    db,
                    user_id=user_id,
                    target_type=r.target_type,
                    target_identifier=r.target_identifier,
                    message=f"{r.target_identifier} price {ph.close:.2f} {r.comparator} {r.threshold:.2f}",
                    severity="warning",
                    triggered_at=now,
                )

        elif r.rule_type == "daily_change_pct":
            ph2 = (
                db.execute(
                    select(PriceHistory)
                    .where(and_(PriceHistory.symbol == r.target_identifier))
                    .order_by(desc(PriceHistory.timestamp))
                    .limit(2)
                )
                .scalars()
                .all()
            )
            if len(ph2) < 2:
                continue
            last, prev = ph2[0], ph2[1]
            if prev.close == 0:
                continue
            change_pct = (float(last.close) / float(prev.close) - 1.0) * 100.0
            if _cmp(change_pct, r.comparator, float(r.threshold)):
                created += _create_alert(
                    db,
                    user_id=user_id,
                    target_type=r.target_type,
                    target_identifier=r.target_identifier,
                    message=f"{r.target_identifier} daily change {change_pct:.2f}% {r.comparator} {r.threshold:.2f}%",
                    severity="warning" if abs(change_pct) < 4 else "critical",
                    triggered_at=now,
                )

        elif r.rule_type == "prediction_confidence":
            pred = (
                db.execute(
                    select(Prediction)
                    .where(
                        and_(
                            Prediction.target_type == r.target_type,
                            Prediction.target_identifier == r.target_identifier,
                        )
                    )
                    .order_by(desc(Prediction.timestamp_generated))
                    .limit(1)
                )
                .scalars()
                .first()
            )
            if not pred:
                continue
            if r.direction and pred.predicted_direction != r.direction:
                continue
            if _cmp(float(pred.confidence_score), r.comparator, float(r.threshold)):
                created += _create_alert(
                    db,
                    user_id=user_id,
                    target_type=r.target_type,
                    target_identifier=r.target_identifier,
                    message=(
                        f"{r.target_identifier} prediction {pred.predicted_direction} "
                        f"confidence {pred.confidence_score:.2f} {r.comparator} {r.threshold:.2f}"
                    ),
                    severity="info" if float(pred.confidence_score) < 0.8 else "warning",
                    triggered_at=now,
                )

    return created


def _create_alert(
    db: Session,
    *,
    user_id: int,
    target_type: str,
    target_identifier: str,
    message: str,
    severity: str,
    triggered_at: datetime,
) -> int:
    existing = db.execute(
        select(Alert.id).where(
            and_(
                Alert.user_id == user_id,
                Alert.target_type == target_type,
                Alert.target_identifier == target_identifier,
                Alert.message == message,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return 0
    db.add(
        Alert(
            user_id=user_id,
            target_type=target_type,
            target_identifier=target_identifier,
            triggered_at=triggered_at,
            severity=severity,
            message=message,
            is_read=False,
        )
    )
    db.commit()
    return 1

