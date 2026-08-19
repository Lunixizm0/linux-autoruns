from __future__ import annotations

import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class DbusScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "D-Bus"

    @property
    def description(self) -> str:
        return "D-Bus ve Polkit servisleri"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        dirs = [
            "/usr/share/dbus-1/services",
            "/usr/share/dbus-1/system-services",
            os.path.expanduser("~/.local/share/dbus-1/services"),
        ]
        for dirpath in dirs:
            if not self._safe_exists(dirpath):
                continue
            for f in sorted(Path(dirpath).iterdir()):
                if f.suffix == ".service":
                    entry = self._parse_dbus_service(str(f), dirpath)
                    if entry:
                        entries.append(entry)
        policy_dirs = [
            "/etc/dbus-1/system.d",
            os.path.expanduser("~/.local/share/dbus-1/services"),
        ]
        for dirpath in policy_dirs:
            if not self._safe_exists(dirpath):
                continue
            for f in sorted(Path(dirpath).iterdir()):
                if f.suffix == ".conf":
                    entry = self._parse_dbus_policy(str(f))
                    if entry:
                        entries.append(entry)
        return entries

    def _parse_dbus_service(self, path: str, dirpath: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        info = self._get_file_info(path)
        scope = "system" if "system" in dirpath else "user"
        details: dict[str, str | int | bool | list[str]] = {}
        service_name = None
        exec_start = None
        for line in content.splitlines():
            line = line.strip()
            if "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                if key == "Name":
                    service_name = val
                elif key == "Exec":
                    exec_start = val
        details["dbus_type"] = "service"
        return self._make_entry(
            file_path=path,
            name=service_name or Path(path).stem,
            enabled=True,
            command=exec_start,
            scope=scope,
            description="D-Bus service",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["dbus", "service"],
            details=details,
        )

    def _parse_dbus_policy(self, path: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        info = self._get_file_info(path)
        details: dict[str, str | int | bool | list[str]] = {"dbus_type": "policy"}
        return self._make_entry(
            file_path=path,
            name=Path(path).stem,
            enabled=True,
            scope="system",
            description="D-Bus policy config",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["dbus", "policy"],
            details=details,
        )
