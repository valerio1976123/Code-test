from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ExecutionOut(BaseModel):
    id: int
    device_id: int
    schedule_id: int | None
    status: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    output_path: str | None
    error_message: str | None

    class Config:
        from_attributes = True
