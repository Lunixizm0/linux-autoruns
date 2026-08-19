from __future__ import annotations

import os
import re
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class GrubScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "GRUB"

    @property
    def description(self) -> str:
        return "GRUB boot scriptleri"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        entries.extend(self._scan_grub_d())
        entries.extend(self._scan_grub_cfg())
        return entries

    def _scan_grub_d(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        grub_d = "/etc/grub.d"
        if not self._safe_exists(grub_d):
            return entries
        for f in sorted(Path(grub_d).iterdir()):
            if f.is_file() and os.access(str(f), os.X_OK):
                info = self._get_file_info(str(f))
                content = self._read_file(str(f))
                description = None
                if content:
                    for line in content.splitlines()[:10]:
                        if "description" in line.lower() or "# " in line:
                            description = line.strip("# !")
                            break
                entries.append(self._make_entry(
                    file_path=str(f),
                    name=f.name,
                    enabled=True,
                    scope="system",
                    description=description or f"GRUB script: {f.name}",
                    last_modified=self._get_mtime_iso(str(f)),
                    file_size=info["size"],
                    file_permissions=info["permissions"],
                    owner=info["owner"],
                    tags=["boot", "grub"],
                    details={"script_type": "grub.d", "executable": True},
                ))
        return entries

    def _scan_grub_cfg(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        grub_cfg = "/boot/grub/grub.cfg"
        if not self._safe_exists(grub_cfg):
            return entries
        content = self._read_file(grub_cfg)
        if not content:
            return entries
        info = self._get_file_info(grub_cfg)
        menu_entries = re.findall(r"menuentry\s+['\"](.+?)['\"]", content)
        default = None
        for line in content.splitlines():
            if "set default=" in line:
                default = line.split("=", 1)[1].strip().strip('"')
        details: dict[str, str | int | bool | list[str]] = {
            "menu_entries": menu_entries,
            "default_entry": default,
            "menu_entry_count": len(menu_entries),
        }
        entries.append(self._make_entry(
            file_path=grub_cfg,
            name="grub.cfg",
            enabled=True,
            scope="system",
            description=f"GRUB config ({len(menu_entries)} entries)",
            last_modified=self._get_mtime_iso(grub_cfg),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["boot", "grub"],
            details=details,
        ))
        return entries
