from __future__ import annotations

import json
from typing import Any


def commands_for_vendor(vendor: str, command_profile_json: str | None = None) -> list[str]:
    v = (vendor or "generic").strip().lower()

    if v in {"cisco", "cisco_ios", "ios", "nxos", "cisco_nxos"}:
        return [
            "terminal length 0",
            "show running-config",
        ]

    if v in {"paloalto", "panos", "palo_alto"}:
        return [
            "set cli pager off",
            "show config running",
        ]

    if v in {"fortigate", "fortinet"}:
        return [
            "show full-configuration",
        ]

    if v in {"mikrotik", "routeros"}:
        return [
            "export",
        ]

    # generic
    if command_profile_json:
        try:
            data: Any = json.loads(command_profile_json)
            if isinstance(data, dict) and isinstance(data.get("commands"), list):
                cmds = [str(x) for x in data["commands"] if str(x).strip()]
                if cmds:
                    return cmds
        except Exception:
            pass

    return ["show running-config"]
