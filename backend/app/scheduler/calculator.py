from __future__ import annotations

from datetime import date, datetime, time, timedelta


def _coerce_time(t: time | None) -> time:
    return t or time(0, 0, 0)


def compute_next_run_at(
    *,
    schedule_type: str,
    now: datetime,
    run_once_at: datetime | None = None,
    time_of_day: time | None = None,
    weekdays_csv: str | None = None,
    every_n_hours: int | None = None,
    last_run_at: datetime | None = None,
) -> datetime | None:
    st = (schedule_type or "").lower().strip()

    if st == "run_once":
        if run_once_at is None:
            return None
        return run_once_at if run_once_at > now else None

    if st == "every_n_hours":
        n = every_n_hours or 0
        if n <= 0:
            return None
        base = last_run_at or now
        next_at = base + timedelta(hours=n)
        return next_at if next_at > now else now + timedelta(hours=n)

    tod = _coerce_time(time_of_day)

    if st == "daily":
        today = datetime.combine(date=now.date(), time=tod)
        return today if today > now else today + timedelta(days=1)

    if st == "weekly":
        # weekdays 0..6 (Mon..Sun)
        if not weekdays_csv:
            return None
        try:
            days = sorted({int(x) for x in weekdays_csv.split(",") if x.strip() != ""})
        except Exception:
            return None
        days = [d for d in days if 0 <= d <= 6]
        if not days:
            return None

        # search next occurrence within next 7 days
        for add in range(0, 8):
            d = now.date() + timedelta(days=add)
            if d.weekday() not in days:
                continue
            candidate = datetime.combine(date=d, time=tod)
            if candidate > now:
                return candidate
        # fallback one week later
        d = now.date() + timedelta(days=7)
        return datetime.combine(date=d, time=tod)

    return None
