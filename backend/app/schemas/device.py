from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DeviceBase(BaseModel):
    name: str
    host: str
    port: int = 22
    vendor: str = "generic"
    username: str = ""
    is_enabled: bool = False
    command_profile_json: str | None = None


class DeviceCreate(DeviceBase):
    password: str | None = None
    enable_secret: str | None = None
    passphrase: str | None = None


class DeviceUpdate(BaseModel):
    name: str | None = None
    host: str | None = None
    port: int | None = None
    vendor: str | None = None
    username: str | None = None
    is_enabled: bool | None = None
    command_profile_json: str | None = None

    password: str | None = None
    enable_secret: str | None = None
    passphrase: str | None = None


class DeviceOut(DeviceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
