from __future__ import annotations

import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class X11Scanner(BaseScanner):
    @property
    def name(self) -> str:
        return "X11"

    @property
    def description(self) -> str:
        return "X11 session ve display manager autostart"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        home = os.path.expanduser("~")
        x11_files = [
            f"{home}/.xinitrc",
            f"{home}/.xsession",
            f"{home}/.xprofile",
            f"{home}/.Xsession",
        ]
        for path in x11_files:
            if self._safe_exists(path):
                entry = self._make_x11_entry(path, "user")
                if entry:
                    entries.append(entry)
        xsession_d = "/etc/X11/Xsession.d"
        if self._safe_exists(xsession_d):
            for f in sorted(Path(xsession_d).iterdir()):
                if f.is_file():
                    entry = self._make_x11_entry(str(f), "system")
                    if entry:
                        entries.append(entry)
        xsession = "/etc/X11/Xsession"
        if self._safe_exists(xsession):
            entry = self._make_x11_entry(xsession, "system")
            if entry:
                entries.append(entry)
        return entries

    def _make_x11_entry(self, path: str, scope: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        info = self._get_file_info(path)
        sourced = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for prefix in ["source ", ". "]:
                if line.startswith(prefix):
                    src = line[len(prefix):].strip()
                    sourced.append(src)
        details: dict[str, str | int | bool | list[str]] = {}
        if sourced:
            details["sourced_files"] = sourced
        return self._make_entry(
            file_path=path,
            name=Path(path).name,
            enabled=True,
            user=self._current_user if scope == "user" else None,
            scope=scope,
            description=f"X11 session script",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["x11", "session"],
            details=details,
        )
