from __future__ import annotations

import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class UdevScanner(BaseScanner):
    RULE_DIRS = [
        "/etc/udev/rules.d",
        "/run/udev/rules.d",
        "/usr/lib/udev/rules.d",
    ]

    @property
    def name(self) -> str:
        return "Udev"

    @property
    def description(self) -> str:
        return "Udev hardware trigger kuralları"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        for dirpath in self.RULE_DIRS:
            if not self._safe_exists(dirpath):
                continue
            for f in sorted(Path(dirpath).iterdir()):
                if f.is_file() and f.suffix == ".rules":
                    entry = self._parse_rule(str(f))
                    if entry:
                        entries.append(entry)
        return entries

    def _parse_rule(self, path: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        info = self._get_file_info(path)
        rules = []
        actions = set()
        subsystems = set()
        run_commands = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rules.append(line)
            for part in line.split(","):
                part = part.strip()
                if part.startswith("ACTION=="):
                    val = part.split("==")[1].strip('"')
                    actions.add(val)
                elif part.startswith("SUBSYSTEM=="):
                    val = part.split("==")[1].strip('"')
                    subsystems.add(val)
                elif part.startswith("RUN+=" or part.startswith("RUN==")):
                    val = part.split("+")[1].strip('"') if "+" in part else part.split("==")[1].strip('"')
                    run_commands.append(val)
        enabled = len(rules) > 0
        details: dict[str, str | int | bool | list[str]] = {
            "rule_count": len(rules),
        }
        if actions:
            details["actions"] = list(actions)
        if subsystems:
            details["subsystems"] = list(subsystems)
        if run_commands:
            details["run_commands"] = run_commands
        return self._make_entry(
            file_path=path,
            name=Path(path).name,
            enabled=enabled,
            command=run_commands[0] if run_commands else None,
            scope="system",
            description=f"Udev rule ({len(rules)} rules)",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["hw-trigger", "udev"],
            details=details,
        )
