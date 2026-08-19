from __future__ import annotations

import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class KernelScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Kernel"

    @property
    def description(self) -> str:
        return "Sysctl ve proc parametreleri"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        entries.extend(self._scan_sysctl_conf())
        entries.extend(self._scan_sysctl_d())
        return entries

    def _scan_sysctl_conf(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        path = "/etc/sysctl.conf"
        if not self._safe_exists(path):
            return entries
        content = self._read_file(path)
        if not content:
            return entries
        info = self._get_file_info(path)
        params = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                params[key.strip()] = val.strip()
        entries.append(self._make_entry(
            file_path=path,
            name="sysctl.conf",
            enabled=len(params) > 0,
            scope="system",
            description=f"Sysctl config ({len(params)} params)",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["kernel", "sysctl"],
            details={"params": params, "param_count": len(params)},
        ))
        return entries

    def _scan_sysctl_d(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        sysctl_d = "/etc/sysctl.d"
        if not self._safe_exists(sysctl_d):
            return entries
        for f in sorted(Path(sysctl_d).iterdir()):
            if f.is_file() and (f.suffix == ".conf" or f.suffix == ""):
                content = self._read_file(str(f))
                if not content:
                    continue
                info = self._get_file_info(str(f))
                params = {}
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, val = line.partition("=")
                        params[key.strip()] = val.strip()
                if params:
                    entries.append(self._make_entry(
                        file_path=str(f),
                        name=f.name,
                        enabled=True,
                        scope="system",
                        description=f"Sysctl drop-in ({len(params)} params)",
                        last_modified=self._get_mtime_iso(str(f)),
                        file_size=info["size"],
                        file_permissions=info["permissions"],
                        owner=info["owner"],
                        tags=["kernel", "sysctl"],
                        details={"params": params, "param_count": len(params)},
                    ))
        return entries
