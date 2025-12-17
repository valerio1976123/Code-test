from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BackupSchedule(Base):
    __tablename__ = "backup_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)

    device_id: Mapped[int] = mapped_column(ForeignKey("network_devices.id", ondelete="CASCADE"), index=True)

    schedule_type: Mapped[str] = mapped_column(String(50))  # run_once|daily|weekly|every_n_hours

    # schedule params
    run_once_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    time_of_day: Mapped[time | None] = mapped_column(Time, nullable=True)  # for daily/weekly
    weekdays: Mapped[str | None] = mapped_column(String(50), nullable=True)  # CSV: 0(Mon)..6(Sun)
    every_n_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
