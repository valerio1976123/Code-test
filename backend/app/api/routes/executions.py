from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.execution import BackupExecution
from app.schemas.execution import ExecutionOut

router = APIRouter()


@router.get("", response_model=list[ExecutionOut])
def list_executions(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
    device_id: int | None = None,
    schedule_id: int | None = None,
    status: str | None = None,
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    limit: int = 100,
) -> list[ExecutionOut]:
    stmt = select(BackupExecution)
    if device_id is not None:
        stmt = stmt.where(BackupExecution.device_id == device_id)
    if schedule_id is not None:
        stmt = stmt.where(BackupExecution.schedule_id == schedule_id)
    if status is not None:
        stmt = stmt.where(BackupExecution.status == status)
    if created_from is not None:
        stmt = stmt.where(BackupExecution.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(BackupExecution.created_at <= created_to)

    stmt = stmt.order_by(BackupExecution.created_at.desc()).limit(max(1, min(limit, 500)))
    return [ExecutionOut.model_validate(x) for x in db.execute(stmt).scalars().all()]


@router.get("/{execution_id}", response_model=ExecutionOut)
def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> ExecutionOut:
    exe = db.get(BackupExecution, execution_id)
    if not exe:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ExecutionOut.model_validate(exe)


@router.get("/{execution_id}/download")
def download_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> FileResponse:
    exe = db.get(BackupExecution, execution_id)
    if not exe or not exe.output_path:
        raise HTTPException(status_code=404, detail="Backup file not available")
    p = Path(exe.output_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Backup file not found")
    return FileResponse(path=str(p), filename=p.name, media_type="text/plain")
