from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.device import NetworkDevice
from app.models.execution import BackupExecution

router = APIRouter()


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> dict:
    total_devices = db.execute(select(func.count(NetworkDevice.id))).scalar_one()
    enabled_devices = db.execute(select(func.count(NetworkDevice.id)).where(NetworkDevice.is_enabled.is_(True))).scalar_one()

    since = datetime.utcnow() - timedelta(days=1)
    exec_total_24h = db.execute(select(func.count(BackupExecution.id)).where(BackupExecution.created_at >= since)).scalar_one()
    exec_failed_24h = db.execute(
        select(func.count(BackupExecution.id))
        .where(BackupExecution.created_at >= since)
        .where(BackupExecution.status == "failed")
    ).scalar_one()

    recent = db.execute(
        select(BackupExecution).order_by(BackupExecution.created_at.desc()).limit(10)
    ).scalars().all()

    return {
        "devices": {
            "total": total_devices,
            "enabled": enabled_devices,
            "disabled": total_devices - enabled_devices,
        },
        "executions_last_24h": {
            "total": exec_total_24h,
            "failed": exec_failed_24h,
            "success": max(0, exec_total_24h - exec_failed_24h),
        },
        "recent_executions": [
            {
                "id": e.id,
                "device_id": e.device_id,
                "schedule_id": e.schedule_id,
                "status": e.status,
                "created_at": e.created_at,
                "started_at": e.started_at,
                "finished_at": e.finished_at,
                "output_path": e.output_path,
                "error_message": e.error_message,
            }
            for e in recent
        ],
    }
