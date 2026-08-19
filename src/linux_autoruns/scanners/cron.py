from __future__ import annotations

import os
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
        return "Cron jobs"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        entries.extend(self._scan_crontab())
        entries.extend(self._scan_dir("/etc/cron.d", "system"))
        entries.extend(self._scan_spool())
        entries.extend(self._scan_all_user_crontabs())
        for period in ["hourly", "daily", "weekly", "monthly"]:
            cron_dir = f"/etc/cron.{period}"
            if self._safe_exists(cron_dir):
                for f in sorted(Path(cron_dir).iterdir()):
                    if f.is_file() and os.access(str(f), os.X_OK):
                        info = self._get_file_info(str(f))
                        content = self._read_file(str(f))
                        description = None
                        if content:
                            for line in content.splitlines()[:10]:
                                line = line.strip()
                                if line and not line.startswith("#") and not line.startswith("!"):
                                    description = f"Runs {period}: {line[:60]}"
                                    break
                        if not description:
                            description = f"Runs {period}"
                        command = None
                        if content:
                            lines = content.splitlines()
                            if lines and lines[0].startswith("#!"):
                                command = lines[0]
                        entries.append(self._make_entry(
                            file_path=str(f),
                            name=f.name,
                            enabled=True,
                            command=command or str(f),
                            scope="system",
                            description=description,
                            last_modified=self._get_mtime_iso(str(f)),
                            file_size=info["size"],
                            file_permissions=info["permissions"],
                            owner=info["owner"],
                            tags=["scheduled", "cron", period],
                            details={"schedule_type": period, "source": "cron." + period},
                        ))
        return entries

    def _scan_crontab(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        content = self._read_file("/etc/crontab")
        if content:
            entries.extend(self._parse_cron_file_content("/etc/crontab", content, "system"))
        return entries

    def _scan_all_user_crontabs(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        is_root = os.geteuid() == 0
        if is_root:
            try:
                result = subprocess.run(
                    ["crontab", "-l"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    entries.extend(self._parse_cron_file_content(
                        "root-crontab", result.stdout, "user", user="root"
                    ))
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            try:
                passwd = self._read_file("/etc/passwd")
                if passwd:
                    for line in passwd.splitlines():
                        parts = line.split(":")
                        if len(parts) >= 1:
                            username = parts[0]
                            if username in ("root", ""):
                                continue
                            try:
                                r = subprocess.run(
                                    ["crontab", "-l", "-u", username],
                                    capture_output=True, text=True, timeout=5
                                )
                                if r.returncode == 0 and r.stdout.strip():
                                    entries.extend(self._parse_cron_file_content(
                                        f"crontab-{username}", r.stdout, "user", user=username
                                    ))
                            except (FileNotFoundError, subprocess.TimeoutExpired):
                                continue
            except (OSError, PermissionError):
                pass
        else:
            try:
                result = subprocess.run(
                    ["crontab", "-l"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    entries.extend(self._parse_cron_file_content(
                        "current-user-crontab", result.stdout, "user",
                        user=os.environ.get("USER", "unknown")
                    ))
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
                    entries.extend(self._parse_cron_file_content(
                        str(f), content, "user", user=f.name
                    ))
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
        if not content:
            return entries
        has_user_field = path in ("/etc/crontab",) or "/etc/cron.d/" in path
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("@"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            minute, hour, dom, month, dow = parts[:5]
            cron_fields = [minute, hour, dom, month, dow]
            if not all(f.replace("*", "").replace("/", "").replace(",", "").replace("-", "").isdigit() or f == "*" for f in cron_fields):
                continue
            if has_user_field:
                if len(parts) < 7:
                    continue
                cmd_user = parts[5]
                command = " ".join(parts[6:])
            else:
                cmd_user = user or "unknown"
                command = " ".join(parts[5:])
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
