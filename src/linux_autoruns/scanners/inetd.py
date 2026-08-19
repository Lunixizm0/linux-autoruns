from __future__ import annotations

import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class InetdScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "inetd/xinetd"

    @property
    def description(self) -> str:
        return "inetd ve xinetd servisleri"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        entries.extend(self._scan_inetd())
        entries.extend(self._scan_xinetd())
        return entries

    def _scan_inetd(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        conf = "/etc/inetd.conf"
        if not self._safe_exists(conf):
            return entries
        content = self._read_file(conf)
        if not content:
            return entries
        info = self._get_file_info(conf)
        services = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 3:
                services.append({"name": parts[0], "type": parts[1], "server": parts[2] if len(parts) > 3 else parts[2]})
        if services:
            entries.append(self._make_entry(
                file_path=conf,
                name="inetd.conf",
                enabled=True,
                command=services[0]["server"] if services else None,
                scope="system",
                description=f"inetd config ({len(services)} services)",
                last_modified=self._get_mtime_iso(conf),
                file_size=info["size"],
                file_permissions=info["permissions"],
                owner=info["owner"],
                tags=["inetd", "network"],
                details={"services": [s["name"] for s in services], "service_count": len(services)},
            ))
        return entries

    def _scan_xinetd(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        xinetd_conf = "/etc/xinetd.conf"
        if self._safe_exists(xinetd_conf):
            entry = self._parse_xinetd_conf(xinetd_conf)
            if entry:
                entries.append(entry)
        xinetd_d = "/etc/xinetd.d"
        if self._safe_exists(xinetd_d):
            for f in sorted(Path(xinetd_d).iterdir()):
                if f.is_file():
                    entry = self._parse_xinetd_service(str(f))
                    if entry:
                        entries.append(entry)
        return entries

    def _parse_xinetd_conf(self, path: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        info = self._get_file_info(path)
        return self._make_entry(
            file_path=path,
            name="xinetd.conf",
            enabled=True,
            scope="system",
            description="xinetd main config",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["xinetd", "network"],
            details={"config_type": "main"},
        )

    def _parse_xinetd_service(self, path: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        info = self._get_file_info(path)
        details: dict[str, str | int | bool | list[str]] = {}
        current_section = None
        for line in content.splitlines():
            line = line.strip()
            if "{" in line:
                current_section = line.split("{")[0].strip()
                continue
            if line == "}":
                current_section = None
                continue
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                details[key] = val
        enabled = details.get("disable", "yes") != "yes"
        return self._make_entry(
            file_path=path,
            name=Path(path).name,
            enabled=enabled,
            command=details.get("server"),
            scope="system",
            description=f"xinetd service: {current_section or Path(path).stem}",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["xinetd", "network"],
            details=details,
        )
