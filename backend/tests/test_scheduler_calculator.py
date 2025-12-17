from __future__ import annotations

from datetime import datetime, time

from app.scheduler.calculator import compute_next_run_at


def test_next_run_daily() -> None:
    now = datetime(2025, 1, 1, 1, 0, 0)
    nxt = compute_next_run_at(schedule_type="daily", now=now, time_of_day=time(2, 0, 0))
    assert nxt == datetime(2025, 1, 1, 2, 0, 0)


def test_next_run_daily_rollover() -> None:
    now = datetime(2025, 1, 1, 3, 0, 0)
    nxt = compute_next_run_at(schedule_type="daily", now=now, time_of_day=time(2, 0, 0))
    assert nxt == datetime(2025, 1, 2, 2, 0, 0)


def test_next_run_weekly() -> None:
    # 2025-01-01 is Wednesday (weekday=2)
    now = datetime(2025, 1, 1, 1, 0, 0)
    nxt = compute_next_run_at(schedule_type="weekly", now=now, time_of_day=time(2, 0, 0), weekdays_csv="2,4")
    assert nxt == datetime(2025, 1, 1, 2, 0, 0)


def test_next_run_every_n_hours() -> None:
    now = datetime(2025, 1, 1, 0, 0, 0)
    nxt = compute_next_run_at(schedule_type="every_n_hours", now=now, every_n_hours=6, last_run_at=now)
    assert nxt == datetime(2025, 1, 1, 6, 0, 0)


def test_next_run_run_once_past_is_none() -> None:
    now = datetime(2025, 1, 2, 0, 0, 0)
    nxt = compute_next_run_at(schedule_type="run_once", now=now, run_once_at=datetime(2025, 1, 1, 0, 0, 0))
    assert nxt is None
