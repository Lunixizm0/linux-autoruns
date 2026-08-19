from __future__ import annotations

import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class ShellScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Shell Profile"

    @property
    def description(self) -> str:
        return "Shell profile ve login scriptleri"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        home = os.path.expanduser("~")
        shell_files = {
            f"{home}/.bashrc": "bash",
            f"{home}/.bash_profile": "bash",
            f"{home}/.profile": "generic",
            f"{home}/.bash_login": "bash",
            f"{home}/.zshrc": "zsh",
            f"{home}/.zprofile": "zsh",
            f"{home}/.zlogin": "zsh",
            "/etc/profile": "generic",
            "/etc/bash.bashrc": "bash",
        }
        for path, shell in shell_files.items():
            if self._safe_exists(path):
                entry = self._make_shell_entry(path, shell)
                if entry:
                    entries.append(entry)
        profile_d = "/etc/profile.d"
        if self._safe_exists(profile_d):
            for f in sorted(Path(profile_d).glob("*.sh")):
                entry = self._make_shell_entry(str(f), "generic")
                if entry:
                    entries.append(entry)
        fish_conf_d = os.path.expanduser("~/.config/fish/conf.d")
        if self._safe_exists(fish_conf_d):
            for f in sorted(Path(fish_conf_d).iterdir()):
                if f.is_file():
                    entry = self._make_shell_entry(str(f), "fish")
                    if entry:
                        entries.append(entry)
        fish_config = os.path.expanduser("~/.config/fish/config.fish")
        if self._safe_exists(fish_config):
            entry = self._make_shell_entry(fish_config, "fish")
            if entry:
                entries.append(entry)
        return entries

    def _make_shell_entry(self, path: str, shell: str) -> AutostartEntry | None:
        content = self._read_file(path)
        if not content:
            return None
        sourced = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for prefix in ["source ", ". "]:
                if line.startswith(prefix):
                    src = line[len(prefix):].strip()
                    if src.startswith("~"):
                        src = os.path.expanduser(src)
                    elif not src.startswith("/"):
                        src = os.path.join(os.path.dirname(path), src)
                    sourced.append(src)
        info = self._get_file_info(path)
        scope = "system" if path.startswith("/etc/") else "user"
        user = os.environ.get("USER") if scope == "user" else None
        details: dict[str, str | int | bool | list[str]] = {"shell": shell}
        if sourced:
            details["sourced_files"] = sourced
        return self._make_entry(
            file_path=path,
            name=Path(path).name,
            enabled=True,
            command=content.splitlines()[0] if content and content.startswith("#!") else None,
            user=user,
            scope=scope,
            description=f"{shell} profile script",
            last_modified=self._get_mtime_iso(path),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["login", "shell"],
            details=details,
        )
