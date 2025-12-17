from __future__ import annotations

from datetime import datetime, time

from pydantic import BaseModel


class ScheduleBase(BaseModel):
    name: str
    device_id: int
    schedule_type: str

    run_once_at: datetime | None = None
    time_of_day: time | None = None
    weekdays: str | None = None
    every_n_hours: int | None = None

    is_enabled: bool = True


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    name: str | None = None
    device_id: int | None = None
    schedule_type: str | None = None

    run_once_at: datetime | None = None
    time_of_day: time | None = None
    weekdays: str | None = None
    every_n_hours: int | None = None

    is_enabled: bool | None = None


class ScheduleOut(ScheduleBase):
    id: int
    next_run_at: datetime | None
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
