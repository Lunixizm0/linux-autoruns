from __future__ import annotations

import configparser
import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class DisplayManagerScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Display Manager"

    @property
    def description(self) -> str:
        return "GDM, LightDM, SDDM login manager"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        entries.extend(self._scan_gdm())
        entries.extend(self._scan_lightdm())
        entries.extend(self._scan_sddm())
        entries.extend(self._scan_slim())
        return entries

    def _scan_gdm(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        for gdm_dir in ["/etc/gdm", "/etc/gdm3"]:
            if not self._safe_exists(gdm_dir):
                continue
            for f in sorted(Path(gdm_dir).rglob("*.conf")):
                entry = self._parse_config(str(f), "GDM")
                if entry:
                    entries.append(entry)
            custom = Path(gdm_dir) / "custom.conf"
            if custom.exists():
                entry = self._parse_config(str(custom), "GDM")
                if entry:
                    entries.append(entry)
        return entries

    def _scan_lightdm(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        conf = "/etc/lightdm/lightdm.conf"
        if self._safe_exists(conf):
            entry = self._parse_lightdm_conf(conf)
            if entry:
                entries.append(entry)
        return entries

    def _scan_sddm(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        conf = "/etc/sddm.conf"
        if self._safe_exists(conf):
            entry = self._parse_config(conf, "SDDM")
            if entry:
                entries.append(entry)
        conf_d = "/etc/sddm.conf.d"
        if self._safe_exists(conf_d):
            for f in sorted(Path(conf_d).iterdir()):
                if f.suffix == ".conf":
                    entry = self._parse_config(str(f), "SDDM")
                    if entry:
                        entries.append(entry)
        return entries

    def _scan_slim(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        conf = "/etc/slim.conf"
        if self._safe_exists(conf):
            entry = self._parse_config(conf, "SLiM")
            if entry:
                entries.append(entry)
        return entries

    def _parse_config(self, path: str, dm_name: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        info = self._get_file_info(path)
        details: dict[str, str | int | bool | list[str]] = {"display_manager": dm_name}
        current_section = None
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                details.setdefault("sections", [])
                if isinstance(details["sections"], list):
                    details["sections"].append(current_section)
                continue
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                details[key] = val
        return self._make_entry(
            file_path=path,
            name=f"{dm_name} config",
            enabled=True,
            scope="system",
            description=f"{dm_name} display manager config",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["display-manager", dm_name.lower()],
            details=details,
        )

    def _parse_lightdm_conf(self, path: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        info = self._get_file_info(path)
        details: dict[str, str | int | bool | list[str]] = {"display_manager": "LightDM"}
        for line in content.splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                details[key.strip()] = val.strip()
        return self._make_entry(
            file_path=path,
            name="LightDM config",
            enabled=True,
            scope="system",
            description="LightDM display manager config",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["display-manager", "lightdm"],
            details=details,
        )
