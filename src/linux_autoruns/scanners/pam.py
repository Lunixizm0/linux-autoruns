from __future__ import annotations

import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class PAMScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "PAM"

    @property
    def description(self) -> str:
        return "PAM login config"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        pam_conf = "/etc/pam.conf"
        if self._safe_exists(pam_conf):
            entry = self._parse_pam_file(pam_conf, "system")
            if entry:
                entries.append(entry)
        pam_d = "/etc/pam.d"
        if self._safe_exists(pam_d):
            for f in sorted(Path(pam_d).iterdir()):
                if f.is_file():
                    entry = self._parse_pam_file(str(f), "system")
                    if entry:
                        entries.append(entry)
        return entries

    def _parse_pam_file(self, path: str, scope: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        info = self._get_file_info(path)
        rules = []
        modules = set()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 3:
                rules.append(line)
                modules.add(parts[0])
        details: dict[str, str | int | bool | list[str]] = {
            "rule_count": len(rules),
            "modules": list(modules),
        }
        return self._make_entry(
            file_path=path,
            name=Path(path).name,
            enabled=len(rules) > 0,
            scope=scope,
            description=f"PAM config ({len(rules)} rules, {len(modules)} modules)",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["pam", "auth"],
            details=details,
        )
