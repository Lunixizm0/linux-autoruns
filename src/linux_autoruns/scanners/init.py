from __future__ import annotations

import os
import re
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class InitScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "SysVinit"

    @property
    def description(self) -> str:
        return "SysVinit, rc scripts, rc.local"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        entries.extend(self._scan_init_d())
        entries.extend(self._scan_rc_local())
        entries.extend(self._scan_rc_dirs())
        return entries

    def _scan_init_d(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        init_dir = "/etc/init.d"
        if not self._safe_exists(init_dir):
            return entries
        for f in sorted(Path(init_dir).iterdir()):
            if f.is_file() and os.access(str(f), os.X_OK):
                content = self._read_file(str(f))
                description = None
                if content:
                    for line in content.splitlines()[:20]:
                        m = re.search(r"#\s*(?:###?\s*BEGIN\s+INIT\s+INFO)(.+?)(?:###?\s*END\s+INIT\s+INFO)", content, re.DOTALL)
                        if m:
                            block = m.group(1)
                            for bl in block.splitlines():
                                if "Description:" in bl:
                                    description = bl.split("Description:", 1)[1].strip()
                                    break
                            break
                info = self._get_file_info(str(f))
                entries.append(self._make_entry(
                    file_path=str(f),
                    name=f.name,
                    enabled=True,
                    description=description,
                    scope="system",
                    last_modified=self._get_mtime_iso(str(f)),
                    file_size=info["size"],
                    file_permissions=info["permissions"],
                    owner=info["owner"],
                    tags=["boot", "init.d"],
                    details={"init_style": "sysvinit"},
                ))
        return entries

    def _scan_rc_local(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        paths = ["/etc/rc.local", "/etc/rc.d/rc.local"]
        for path in paths:
            if not self._safe_exists(path):
                continue
            content = self._read_file(path)
            enabled = True
            command = None
            if content:
                lines = content.splitlines()
                enabled = "#!/bin/false" not in content
                if len(lines) >= 3:
                    enabled = enabled and "exit 0" not in lines[-3:]
                elif lines:
                    enabled = enabled and "exit 0" not in lines
                cmd_lines = [
                    l for l in lines
                    if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("!")
                ]
                if cmd_lines:
                    command = "\n".join(cmd_lines)
            info = self._get_file_info(path)
            entries.append(self._make_entry(
                file_path=path,
                name=Path(path).name,
                enabled=enabled,
                command=command,
                scope="system",
                last_modified=self._get_mtime_iso(path),
                file_size=info["size"],
                file_permissions=info["permissions"],
                owner=info["owner"],
                tags=["boot", "rc.local"],
                details={"rc_type": "rc.local"},
            ))
        return entries

    def _scan_rc_dirs(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        for runlevel in range(0, 7):
            for prefix_dir in [f"/etc/rc{runlevel}.d", "/etc/rcS.d"]:
                if not self._safe_exists(prefix_dir):
                    continue
                for f in sorted(Path(prefix_dir).iterdir()):
                    if not f.is_symlink():
                        continue
                    target = os.path.realpath(str(f))
                    name = f.name
                    enabled = name.startswith("S")
                    info = self._get_file_info(str(f))
                    entries.append(self._make_entry(
                        file_path=str(f),
                        name=name,
                        enabled=enabled,
                        scope="system",
                        last_modified=self._get_mtime_iso(target),
                        file_size=info["size"],
                        file_permissions=info["permissions"],
                        owner=info["owner"],
                        tags=["boot", "runlevel"],
                        details={
                            "runlevel": runlevel,
                            "target": target,
                            "start_priority": name[1:3] if len(name) > 3 else None,
                        },
                    ))
        return entries
