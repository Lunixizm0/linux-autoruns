from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class CronScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Cron"

    @property
    def description(self) -> str:
        return "Cron job'ları"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        entries.extend(self._scan_crontab())
        entries.extend(self._scan_dir("/etc/cron.d", "system"))
        entries.extend(self._scan_spool())
        for period in ["hourly", "daily", "weekly", "monthly"]:
            cron_dir = f"/etc/cron.{period}"
            if self._safe_exists(cron_dir):
                for f in sorted(Path(cron_dir).iterdir()):
                    if f.is_file():
                        entries.extend(self._parse_cron_file(str(f), f"cron.{period}", "system"))
        return entries

    def _scan_crontab(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        content = self._read_file("/etc/crontab")
        if content:
            entries.extend(self._parse_cron_file_content("/etc/crontab", content, "system"))
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                entries.extend(self._parse_cron_file_content("~/.current-user-crontab", result.stdout, "user", user=os.environ.get("USER")))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return entries

    def _scan_dir(self, dirpath: str, scope: str) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        if not self._safe_exists(dirpath):
            return entries
        for f in sorted(Path(dirpath).iterdir()):
            if f.is_file() and not f.name.startswith("."):
                entries.extend(self._parse_cron_file(str(f), dirpath, scope))
        return entries

    def _scan_spool(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        spool_dir = "/var/spool/cron/crontabs"
        if not self._safe_exists(spool_dir):
            return entries
        for f in sorted(Path(spool_dir).iterdir()):
            if f.is_file():
                content = self._read_file(str(f))
                if content:
                    entries.extend(self._parse_cron_file_content(str(f), content, "user", user=f.name))
        return entries

    def _parse_cron_file(self, path: str, source: str, scope: str) -> list[AutostartEntry]:
        content = self._read_file(path)
        if not content:
            return []
        return self._parse_cron_file_content(path, content, scope)

    def _parse_cron_file_content(
        self, path: str, content: str, scope: str, user: str | None = None
    ) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 6:
                continue
            minute, hour, dom, month, dow = parts[:5]
            cmd_user = user or parts[5]
            command = " ".join(parts[6:]) if len(parts) > 6 else parts[5]
            schedule = f"{minute} {hour} {dom} {month} {dow}"
            info = self._get_file_info(path)
            entries.append(self._make_entry(
                file_path=path,
                name=f"cron:{schedule}",
                enabled=True,
                command=command,
                user=cmd_user,
                scope=scope,
                description=f"Cron schedule: {schedule}",
                last_modified=self._get_mtime_iso(path),
                file_size=info["size"],
                file_permissions=info["permissions"],
                owner=info["owner"],
                tags=["scheduled", "cron"],
                details={
                    "schedule": schedule,
                    "minute": minute,
                    "hour": hour,
                    "day_of_month": dom,
                    "month": month,
                    "day_of_week": dow,
                    "user": cmd_user,
                },
            ))
        return entries
