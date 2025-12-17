from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import paramiko
from sqlalchemy.orm import Session

from app.backup.command_provider import commands_for_vendor
from app.core.config import settings
from app.models.device import NetworkDevice
from app.models.execution import BackupExecution
from app.security.crypto import decrypt_secret


@dataclass(frozen=True)
class BackupResult:
    output_path: str


def build_backup_file_path(*, vendor: str, device_name: str, now: datetime) -> Path:
    ts = now.strftime("%Y-%m-%d_%H-%M-%S")
    root = settings.backup_root_path
    return (
        root
        / (vendor or "generic")
        / device_name
        / now.strftime("%Y")
        / now.strftime("%m")
        / f"{device_name}_{ts}.txt"
    )


def _run_commands_over_ssh(
    *,
    host: str,
    port: int,
    username: str,
    password: str | None,
    commands: list[str],
    timeout: int = 20,
) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(
        hostname=host,
        port=port,
        username=username,
        password=password,
        look_for_keys=False,
        allow_agent=False,
        timeout=timeout,
    )

    try:
        chan = client.invoke_shell(width=200, height=60)
        chan.settimeout(timeout)

        def send(cmd: str) -> None:
            chan.send(cmd.strip() + "\n")

        output_parts: list[str] = []
        # initial read
        try:
            output_parts.append(chan.recv(65535).decode(errors="ignore"))
        except Exception:
            pass

        for cmd in commands:
            send(cmd)
            # naive read loop
            buf = ""
            end_at = datetime.utcnow().timestamp() + timeout
            while datetime.utcnow().timestamp() < end_at:
                try:
                    chunk = chan.recv(65535)
                    if not chunk:
                        break
                    buf += chunk.decode(errors="ignore")
                    # heuristics: stop when prompt seems to reappear
                    if buf.strip().endswith((">", "#", "]#")):
                        break
                except Exception:
                    break
            output_parts.append(f"\n$ {cmd}\n" + buf)

        return "\n".join(output_parts).strip() + "\n"
    finally:
        try:
            client.close()
        except Exception:
            pass


def run_backup_execution(db: Session, execution_id: int) -> BackupResult:
    exe = db.get(BackupExecution, execution_id)
    if not exe:
        raise RuntimeError("Execution not found")

    device = db.get(NetworkDevice, exe.device_id)
    if not device:
        raise RuntimeError("Device not found")

    now = datetime.utcnow()
    exe.status = "running"
    if exe.started_at is None:
        exe.started_at = now
    exe.error_message = None
    db.commit()

    try:
        commands = commands_for_vendor(device.vendor, device.command_profile_json)
        password = decrypt_secret(device.password_enc)

        output = _run_commands_over_ssh(
            host=device.host,
            port=device.port,
            username=device.username,
            password=password,
            commands=commands,
        )

        out_path = build_backup_file_path(vendor=device.vendor, device_name=device.name, now=now)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8", errors="ignore")

        exe.status = "success"
        exe.finished_at = datetime.utcnow()
        exe.output_path = str(out_path)
        db.commit()
        return BackupResult(output_path=str(out_path))

    except Exception as e:
        exe.status = "failed"
        exe.finished_at = datetime.utcnow()
        exe.error_message = str(e)
        db.commit()
        raise
