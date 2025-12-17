from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.device import NetworkDevice
from app.models.schedule import BackupSchedule
from app.models.user import User
from app.scheduler.calculator import compute_next_run_at
from app.security.crypto import encrypt_secret
from app.security.passwords import hash_password


def run_seed() -> None:
    now = datetime.utcnow()
    with SessionLocal() as db:
        # admin user
        admin = db.execute(select(User).where(User.username == "admin")).scalar_one_or_none()
        if not admin:
            admin = User(username="admin", password_hash=hash_password("admin"), is_active=True)
            db.add(admin)

        # devices (disabled)
        devices = [
            ("lab-cisco-1", "192.0.2.10", "cisco_ios"),
            ("lab-forti-1", "192.0.2.20", "fortigate"),
            ("lab-mikro-1", "192.0.2.30", "mikrotik"),
        ]

        created_ids: list[int] = []
        for name, host, vendor in devices:
            existing = db.execute(select(NetworkDevice).where(NetworkDevice.name == name)).scalar_one_or_none()
            if existing:
                created_ids.append(existing.id)
                continue
            d = NetworkDevice(
                name=name,
                host=host,
                port=22,
                vendor=vendor,
                username="admin",
                password_enc=encrypt_secret("password"),
                is_enabled=False,
            )
            db.add(d)
            db.flush()
            created_ids.append(d.id)

        # example schedule (daily 02:00 UTC) for first device
        if created_ids:
            existing_s = db.execute(select(BackupSchedule).where(BackupSchedule.name == "Example Daily Backup")).scalar_one_or_none()
            if not existing_s:
                sch = BackupSchedule(
                    name="Example Daily Backup",
                    device_id=created_ids[0],
                    schedule_type="daily",
                    time_of_day=time(2, 0, 0),
                    is_enabled=True,
                )
                sch.next_run_at = compute_next_run_at(
                    schedule_type=sch.schedule_type,
                    now=now,
                    time_of_day=sch.time_of_day,
                    weekdays_csv=sch.weekdays,
                    every_n_hours=sch.every_n_hours,
                    run_once_at=sch.run_once_at,
                    last_run_at=None,
                )
                db.add(sch)

        db.commit()


if __name__ == "__main__":
    run_seed()
    print("Seed completed. Login with admin/admin")
