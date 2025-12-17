from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.device import NetworkDevice
from app.models.execution import BackupExecution
from app.schemas.device import DeviceCreate, DeviceOut, DeviceUpdate
from app.security.crypto import encrypt_secret
from app.scheduler.service import scheduler_service

router = APIRouter()


@router.get("", response_model=list[DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
    q: str | None = None,
    enabled: bool | None = None,
) -> list[DeviceOut]:
    stmt = select(NetworkDevice)
    if q:
        stmt = stmt.where(NetworkDevice.name.ilike(f"%{q}%"))
    if enabled is not None:
        stmt = stmt.where(NetworkDevice.is_enabled.is_(enabled))
    stmt = stmt.order_by(NetworkDevice.name.asc())
    return [DeviceOut.model_validate(x) for x in db.execute(stmt).scalars().all()]


@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> DeviceOut:
    existing = db.execute(select(NetworkDevice).where(NetworkDevice.name == data.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Device name already exists")

    d = NetworkDevice(
        name=data.name,
        host=data.host,
        port=data.port,
        vendor=data.vendor,
        username=data.username,
        is_enabled=data.is_enabled,
        command_profile_json=data.command_profile_json,
        password_enc=encrypt_secret(data.password),
        enable_secret_enc=encrypt_secret(data.enable_secret),
        passphrase_enc=encrypt_secret(data.passphrase),
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return DeviceOut.model_validate(d)


@router.put("/{device_id}", response_model=DeviceOut)
def update_device(
    device_id: int,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> DeviceOut:
    d = db.get(NetworkDevice, device_id)
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")

    for field in ["name", "host", "port", "vendor", "username", "is_enabled", "command_profile_json"]:
        v = getattr(data, field)
        if v is not None:
            setattr(d, field, v)

    if data.password is not None:
        d.password_enc = encrypt_secret(data.password)
    if data.enable_secret is not None:
        d.enable_secret_enc = encrypt_secret(data.enable_secret)
    if data.passphrase is not None:
        d.passphrase_enc = encrypt_secret(data.passphrase)

    db.commit()
    db.refresh(d)
    return DeviceOut.model_validate(d)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> Response:
    d = db.get(NetworkDevice, device_id)
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(d)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{device_id}/run-now", response_model=dict)
def run_now(
    device_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> dict:
    d = db.get(NetworkDevice, device_id)
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")

    exe = BackupExecution(device_id=device_id, schedule_id=None, status="queued")
    db.add(exe)
    db.commit()
    db.refresh(exe)
    scheduler_service.dispatch_execution(exe.id)
    return {"execution_id": exe.id}
