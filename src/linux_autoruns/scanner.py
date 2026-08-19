from __future__ import annotations

import functools
import glob
import os
import stat
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from .models import AutostartEntry

MAX_FILE_SIZE = 1 * 1024 * 1024 * 10  # 10MB

class BaseScanner(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    def _current_user(self) -> str | None:
        return os.environ.get("USER") or os.environ.get("LOGNAME")

    @abstractmethod
    def scan(self) -> list[AutostartEntry]: ...

    def _read_file(self, path: str) -> str | None:
        try:
            p = Path(path)
            if p.stat().st_size > MAX_FILE_SIZE:
                return None
            return p.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return None

    def _get_mtime_iso(self, path: str) -> str | None:
        try:
            mtime = os.path.getmtime(path)
            return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        except (OSError, ValueError):
            return None

    @functools.lru_cache(maxsize=256)
    def _get_file_info(self, path: str) -> dict:
        try:
            s = os.stat(path)
            return {
                "size": s.st_size,
                "permissions": stat.filemode(s.st_mode),
                "owner": self._get_owner(s.st_uid),
            }
        except (OSError, ValueError):
            return {"size": None, "permissions": None, "owner": None}

    def _get_owner(self, uid: int) -> str:
        try:
            import pwd
            return pwd.getpwuid(uid).pw_name
        except (KeyError, ImportError):
            return str(uid)

    def _glob_files(self, pattern: str) -> list[str]:
        try:
            return glob.glob(pattern, recursive=False)
        except (OSError, ValueError):
            return []

    def _safe_exists(self, path: str) -> bool:
        try:
            return os.path.exists(path)
        except (OSError, ValueError):
            return False

    def _parse_key_value(self, content: str) -> dict[str, str]:
        result = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip()
        return result

    def _make_entry(self, **kwargs) -> AutostartEntry:
        defaults = {
            "category": self.name,
            "file_path": "",
            "name": "",
            "enabled": True,
            "command": None,
            "exec_args": None,
            "user": None,
            "scope": "system",
            "description": None,
            "comment": None,
            "last_modified": None,
            "file_size": None,
            "file_permissions": None,
            "owner": None,
            "tags": [],
            "details": {},
        }
        defaults.update(kwargs)
        return AutostartEntry(**defaults)
