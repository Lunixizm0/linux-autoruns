from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class SystemdScanner(BaseScanner):
    SERVICE_DIRS = [
        "/etc/systemd/system",
        "/usr/lib/systemd/system",
        "/run/systemd/system",
    ]
    USER_DIRS = [
        os.path.expanduser("~/.config/systemd/user"),
        "/etc/systemd/user",
    ]

    @property
    def name(self) -> str:
        return "Systemd"

    @property
    def description(self) -> str:
        return "Systemd servisleri ve timer'lar"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        for d in self.SERVICE_DIRS:
            entries.extend(self._scan_dir(d, "system"))
        for d in self.USER_DIRS:
            entries.extend(self._scan_dir(d, "user"))
        for entry in entries:
            if entry.file_path:
                symlink = os.path.realpath(entry.file_path)
                if symlink != entry.file_path and self._safe_exists(symlink):
                    entry.details["real_path"] = symlink
        return entries

    def _scan_dir(self, dirpath: str, scope: str) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        if not self._safe_exists(dirpath):
            return entries
        for f in sorted(Path(dirpath).iterdir()):
            if f.is_symlink() and not f.exists():
                continue
            if f.suffix in (".service", ".timer"):
                entry = self._parse_unit(str(f), scope)
                if entry:
                    entries.append(entry)
            wants_dir = f / "wants"
            if wants_dir.is_dir():
                for link in sorted(wants_dir.iterdir()):
                    if link.is_symlink():
                        target = os.path.realpath(str(link))
                        if self._safe_exists(target):
                            entry = self._parse_unit(target, scope)
                            if entry:
                                entry.enabled = True
                                entry.details["wanted_by_dir"] = str(wants_dir)
                                entries.append(entry)
        return entries

    def _parse_unit(self, path: str, scope: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        name = Path(path).name
        unit_type = Path(path).suffix.lstrip(".")
        details: dict[str, str | int | bool | list[str]] = {"unit_type": unit_type}
        command = None
        exec_args = None
        description = None
        wanted_by = None
        after = None
        restart = None
        timeout = None
        enabled = True
        current_section = None
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                continue
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if current_section == "Unit":
                if key == "Description":
                    description = val
                elif key == "After":
                    after = val
                    details["after"] = val
                elif key == "Wants" or key == "Requires":
                    details.setdefault("wants", [])
                    if isinstance(details["wants"], list):
                        details["wants"].append(val)
            elif current_section == "Service":
                if key == "ExecStart":
                    parts = val.split()
                    command = parts[0] if parts else val
                    exec_args = parts[1:] if len(parts) > 1 else None
                elif key == "Restart":
                    restart = val
                    details["restart"] = val
                elif key == "TimeoutStartSec":
                    timeout = val
                    details["timeout"] = val
                elif key == "Type":
                    details["service_type"] = val
                elif key == "User":
                    details["service_user"] = val
            elif current_section == "Install":
                if key == "WantedBy":
                    wanted_by = val
                    details["wanted_by"] = val
        if wanted_by:
            wanted_path = os.path.join(os.path.dirname(path), f"{wanted_by}.wants", name)
            enabled = self._safe_exists(wanted_path)
        if Path(path).suffix == ".timer":
            enabled = True
        info = self._get_file_info(path)
        tags = ["boot" if scope == "system" else "session"]
        if Path(path).suffix == ".timer":
            tags.append("timer")
        else:
            tags.append("service")
        return self._make_entry(
            file_path=path,
            name=name,
            enabled=enabled,
            command=command,
            exec_args=exec_args,
            description=description,
            scope=scope,
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=tags,
            details=details,
        )
