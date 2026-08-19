from __future__ import annotations

import configparser
import json
import os
import re
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class DesktopEnvScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Desktop Environment"

    @property
    def description(self) -> str:
        return "GNOME, KDE, XFCE, Wayland DE-specific autostart"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        entries.extend(self._scan_gnome())
        entries.extend(self._scan_kde())
        entries.extend(self._scan_xfce())
        entries.extend(self._scan_wayland())
        return entries

    def _scan_gnome(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        gnome_session = os.path.expanduser("~/.config/gnome-session")
        if self._safe_exists(gnome_session):
            for f in sorted(Path(gnome_session).rglob("*")):
                if f.is_file():
                    info = self._get_file_info(str(f))
                    entries.append(self._make_entry(
                        file_path=str(f),
                        name=f.name,
                        enabled=True,
                        user=self._current_user,
                        scope="user",
                        description="GNOME session config",
                        last_modified=self._get_mtime_iso(str(f)),
                        file_size=info["size"],
                        file_permissions=info["permissions"],
                        owner=info["owner"],
                        tags=["gnome", "session"],
                        details={"de": "gnome"},
                    ))
        extensions_dir = os.path.expanduser("~/.local/share/gnome-shell/extensions")
        if self._safe_exists(extensions_dir):
            for d in sorted(Path(extensions_dir).iterdir()):
                if d.is_dir():
                    metadata = d / "metadata.json"
                    ext_name = d.name
                    if metadata.exists():
                        content = self._read_file(str(metadata))
                        if content:
                            try:
                                meta = json.loads(content)
                                ext_name = meta.get("name", d.name)
                            except (json.JSONDecodeError, ValueError):
                                pass
                    info = self._get_file_info(str(d))
                    entries.append(self._make_entry(
                        file_path=str(d),
                        name=ext_name,
                        enabled=True,
                        user=self._current_user,
                        scope="user",
                        description="GNOME shell extension",
                        tags=["gnome", "extension"],
                        details={"de": "gnome", "extension_dir": str(d)},
                    ))
        return entries

    def _scan_kde(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        kde_autostart = os.path.expanduser("~/.kde4/autostart")
        if self._safe_exists(kde_autostart):
            for f in sorted(Path(kde_autostart).iterdir()):
                if f.is_file():
                    info = self._get_file_info(str(f))
                    entries.append(self._make_entry(
                        file_path=str(f),
                        name=f.name,
                        enabled=True,
                        user=self._current_user,
                        scope="user",
                        description="KDE4 autostart",
                        last_modified=self._get_mtime_iso(str(f)),
                        file_size=info["size"],
                        file_permissions=info["permissions"],
                        owner=info["owner"],
                        tags=["kde", "autostart"],
                        details={"de": "kde4"},
                    ))
        plasma_env = os.path.expanduser("~/.config/plasma-workspace/env")
        if self._safe_exists(plasma_env):
            for f in sorted(Path(plasma_env).iterdir()):
                if f.is_file():
                    info = self._get_file_info(str(f))
                    entries.append(self._make_entry(
                        file_path=str(f),
                        name=f.name,
                        enabled=True,
                        user=self._current_user,
                        scope="user",
                        description="Plasma workspace environment",
                        last_modified=self._get_mtime_iso(str(f)),
                        file_size=info["size"],
                        file_permissions=info["permissions"],
                        owner=info["owner"],
                        tags=["kde", "plasma"],
                        details={"de": "plasma"},
                    ))
        kwinrc = os.path.expanduser("~/.config/kwinrc")
        if self._safe_exists(kwinrc):
            content = self._read_file(kwinrc)
            if content:
                cp = configparser.ConfigParser(interpolation=None)
                try:
                    cp.read_string(content)
                except configparser.Error:
                    cp = configparser.ConfigParser()
                info = self._get_file_info(kwinrc)
                entries.append(self._make_entry(
                    file_path=kwinrc,
                    name="kwinrc",
                    enabled=True,
                    user=self._current_user,
                    scope="user",
                    description="KWin window manager config",
                    last_modified=self._get_mtime_iso(kwinrc),
                    file_size=info["size"],
                    file_permissions=info["permissions"],
                    owner=info["owner"],
                    tags=["kde", "kwin"],
                    details={"de": "kde", "sections": cp.sections()},
                ))
        return entries

    def _scan_xfce(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        xfce_conf = os.path.expanduser("~/.config/xfce4/xfconf/xfce-perchannel-xml")
        if self._safe_exists(xfce_conf):
            for f in sorted(Path(xfce_conf).iterdir()):
                if f.suffix == ".xml":
                    info = self._get_file_info(str(f))
                    entries.append(self._make_entry(
                        file_path=str(f),
                        name=f.stem,
                        enabled=True,
                        user=self._current_user,
                        scope="user",
                        description="XFCE session config",
                        last_modified=self._get_mtime_iso(str(f)),
                        file_size=info["size"],
                        file_permissions=info["permissions"],
                        owner=info["owner"],
                        tags=["xfce", "session"],
                        details={"de": "xfce"},
                    ))
        return entries

    def _scan_wayland(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        home = os.path.expanduser("~")
        wayland_configs = {
            f"{home}/.config/sway/config": ("sway", "exec"),
            f"{home}/.config/hyprland/hyprland.conf": ("hyprland", "exec-once"),
        }
        for path, (de, directive) in wayland_configs.items():
            if not self._safe_exists(path):
                continue
            content = self._read_file(path)
            if not content:
                continue
            commands = []
            for line in content.splitlines():
                line = line.strip()
                if line.startswith(directive):
                    cmd = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""
                    commands.append(cmd)
            info = self._get_file_info(path)
            entries.append(self._make_entry(
                file_path=path,
                name=f"{de} config",
                enabled=True,
                user=self._current_user,
                scope="user",
                description=f"{de} wayland compositor config",
                last_modified=self._get_mtime_iso(path),
                file_size=info["size"],
                file_permissions=info["permissions"],
                owner=info["owner"],
                tags=["wayland", de],
                details={"de": de, "autostart_commands": commands, "directive": directive},
            ))
        nwg_autorun = os.path.expanduser("~/.config/nwg-autorun")
        if self._safe_exists(nwg_autorun):
            for f in sorted(Path(nwg_autorun).iterdir()):
                if f.is_file():
                    info = self._get_file_info(str(f))
                    entries.append(self._make_entry(
                        file_path=str(f),
                        name=f.name,
                        enabled=True,
                        user=self._current_user,
                        scope="user",
                        description="nwg-shell autorun",
                        last_modified=self._get_mtime_iso(str(f)),
                        file_size=info["size"],
                        file_permissions=info["permissions"],
                        owner=info["owner"],
                        tags=["wayland", "nwg"],
                        details={"de": "nwg-shell"},
                    ))
        return entries
