from __future__ import annotations

import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class TmpfilesScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "tmpfiles.d"

    @property
    def description(self) -> str:
        return "Systemd tmpfiles.d config"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        dirs = [
            "/etc/tmpfiles.d",
            "/usr/lib/tmpfiles.d",
            os.path.expanduser("~/.local/share/user-tmpfiles.d"),
        ]
        for dirpath in dirs:
            if not self._safe_exists(dirpath):
                continue
            for f in sorted(Path(dirpath).iterdir()):
                if f.is_file():
                    entry = self._parse_tmpfiles(str(f))
                    if entry:
                        entries.append(entry)
        return entries

    def _parse_tmpfiles(self, path: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        info = self._get_file_info(path)
        lines = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            lines.append(line)
        details: dict[str, str | int | bool | list[str]] = {
            "entry_count": len(lines),
        }
        types = set()
        for line in lines:
            parts = line.split()
            if parts:
                types.add(parts[0])
        if types:
            details["types"] = list(types)
        return self._make_entry(
            file_path=path,
            name=Path(path).name,
            enabled=len(lines) > 0,
            scope="system",
            description=f"tmpfiles.d config ({len(lines)} entries)",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["tmpfiles", "systemd"],
            details=details,
        )
