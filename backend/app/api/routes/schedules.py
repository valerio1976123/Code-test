from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.schedule import BackupSchedule
from app.schemas.schedule import ScheduleCreate, ScheduleOut, ScheduleUpdate
from app.scheduler.calculator import compute_next_run_at

router = APIRouter()


@router.get("", response_model=list[ScheduleOut])
def list_schedules(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
    device_id: int | None = None,
    enabled: bool | None = None,
) -> list[ScheduleOut]:
    stmt = select(BackupSchedule)
    if device_id is not None:
        stmt = stmt.where(BackupSchedule.device_id == device_id)
    if enabled is not None:
        stmt = stmt.where(BackupSchedule.is_enabled.is_(enabled))
    stmt = stmt.order_by(BackupSchedule.id.desc())
    return [ScheduleOut.model_validate(x) for x in db.execute(stmt).scalars().all()]


@router.post("", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(
    data: ScheduleCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> ScheduleOut:
    now = datetime.utcnow()
    sch = BackupSchedule(
        name=data.name,
        device_id=data.device_id,
        schedule_type=data.schedule_type,
        run_once_at=data.run_once_at,
        time_of_day=data.time_of_day,
        weekdays=data.weekdays,
        every_n_hours=data.every_n_hours,
        is_enabled=data.is_enabled,
    )
    sch.next_run_at = compute_next_run_at(
        schedule_type=sch.schedule_type,
        now=now,
        run_once_at=sch.run_once_at,
        time_of_day=sch.time_of_day,
        weekdays_csv=sch.weekdays,
        every_n_hours=sch.every_n_hours,
        last_run_at=sch.last_run_at,
    )

    db.add(sch)
    db.commit()
    db.refresh(sch)
    return ScheduleOut.model_validate(sch)


@router.put("/{schedule_id}", response_model=ScheduleOut)
def update_schedule(
    schedule_id: int,
    data: ScheduleUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> ScheduleOut:
    sch = db.get(BackupSchedule, schedule_id)
    if not sch:
        raise HTTPException(status_code=404, detail="Schedule not found")

    for field in [
        "name",
        "device_id",
        "schedule_type",
        "run_once_at",
        "time_of_day",
        "weekdays",
        "every_n_hours",
        "is_enabled",
    ]:
        v = getattr(data, field)
        if v is not None:
            setattr(sch, field, v)

    now = datetime.utcnow()
    sch.next_run_at = compute_next_run_at(
        schedule_type=sch.schedule_type,
        now=now,
        run_once_at=sch.run_once_at,
        time_of_day=sch.time_of_day,
        weekdays_csv=sch.weekdays,
        every_n_hours=sch.every_n_hours,
        last_run_at=sch.last_run_at,
    )

    db.commit()
    db.refresh(sch)
    return ScheduleOut.model_validate(sch)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> Response:
    sch = db.get(BackupSchedule, schedule_id)
    if not sch:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(sch)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
