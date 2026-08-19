from __future__ import annotations

import configparser
import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class XDGScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "XDG Autostart"

    @property
    def description(self) -> str:
        return "XDG autostart .desktop dosyaları"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        dirs = [
            "/etc/xdg/autostart",
            os.path.expanduser("~/.config/autostart"),
        ]
        xdg_config = os.environ.get("XDG_CONFIG_DIRS", "")
        for d in xdg_config.split(":"):
            d = d.strip()
            if d:
                dirs.append(os.path.join(d, "autostart"))
        for dirpath in dirs:
            if not self._safe_exists(dirpath):
                continue
            for f in sorted(Path(dirpath).glob("*.desktop")):
                entry = self._parse_desktop(str(f))
                if entry:
                    entries.append(entry)
        return entries

    def _parse_desktop(self, path: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        cp = configparser.ConfigParser(interpolation=None)
        try:
            cp.read_string(content)
        except configparser.Error:
            return None
        if not cp.has_section("Desktop Entry"):
            return None
        sec = cp["Desktop Entry"]
        hidden = sec.getboolean("Hidden", fallback=False)
        autostart_condition = sec.get("AutostartCondition", None)
        only_show_in = sec.get("OnlyShowIn", None)
        not_show_in = sec.get("NotShowIn", None)
        try:
            args_str = sec.get("Exec", fallback="")
            parts = args_str.split()
            command = parts[0] if parts else None
            exec_args = parts[1:] if len(parts) > 1 else None
        except (ValueError, IndexError):
            command = None
            exec_args = None
        info = self._get_file_info(path)
        details: dict[str, str | int | bool | list[str]] = {}
        if autostart_condition:
            details["autostart_condition"] = autostart_condition
        if only_show_in:
            details["only_show_in"] = only_show_in
        if not_show_in:
            details["not_show_in"] = not_show_in
        type_val = sec.get("Type", None)
        if type_val:
            details["type"] = type_val
        nodisplay = sec.getboolean("Terminal", fallback=False)
        details["terminal"] = nodisplay
        categories = sec.get("Categories", None)
        if categories:
            details["categories"] = categories
        return self._make_entry(
            file_path=path,
            name=Path(path).stem,
            enabled=not hidden,
            command=command,
            exec_args=exec_args,
            description=sec.get("Name", None),
            comment=sec.get("Comment", None),
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["autostart", "desktop"],
            details=details,
        )
