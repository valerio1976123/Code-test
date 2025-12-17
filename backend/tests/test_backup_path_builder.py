from __future__ import annotations

from datetime import datetime

from app.backup.runner import build_backup_file_path


def test_backup_path_builder_shape() -> None:
    now = datetime(2025, 12, 17, 10, 11, 12)
    p = build_backup_file_path(vendor="cisco_ios", device_name="core-sw1", now=now)
    s = str(p).replace("\\", "/")
    assert "backups/" in s  # relative root in settings is ./backups
    assert s.endswith("backups/cisco_ios/core-sw1/2025/12/core-sw1_2025-12-17_10-11-12.txt")
