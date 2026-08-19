from __future__ import annotations

import os
import re

from PySide6.QtCore import (QAbstractTableModel, QModelIndex, Qt,
                            QSortFilterProxyModel)
from PySide6.QtGui import QColor, QFont

from ..models import AutostartEntry
from .theme import CATPPUCCIN_MOCHA

_VALID_KEYS = {
    "name", "category", "user", "owner", "scope",
    "command", "path", "tag", "tags", "description",
}


def _format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return ""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


class EntryTableModel(QAbstractTableModel):
    HEADERS = [
        "+", "Name", "Category", "User", "Description",
        "Command", "Path", "Scope", "Perms", "Size", "Modified", "Owner",
    ]
    _FIELD_MAP = {
        1: "name",
        2: "category",
        3: "user",
        4: "description",
        5: "command",
        6: "file_path",
        7: "scope",
        8: "file_permissions",
        10: "last_modified",
        11: "owner",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[AutostartEntry] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._entries)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        entry = self._entries[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return "+" if entry.enabled else "-"
            if col == 9:
                return _format_size(entry.file_size)
            field = self._FIELD_MAP.get(col)
            if field:
                val = getattr(entry, field, None)
                if val is not None:
                    s = str(val)
                    if col in (5, 6) and len(s) > 50:
                        return s[:47] + "..."
                    return s
                return ""
            return ""

        if role == Qt.TextAlignmentRole:
            if col == 0:
                return int(Qt.AlignCenter)
            if col in (9,):
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

        if role == Qt.ForegroundRole:
            if col == 0:
                color = CATPPUCCIN_MOCHA["green"] if entry.enabled else CATPPUCCIN_MOCHA["red"]
                return QColor(color)
            if col == 1:
                return QColor(CATPPUCCIN_MOCHA["blue"])

        if role == Qt.BackgroundRole:
            if col == 0:
                return None
            if entry.file_path and not os.path.exists(entry.file_path):
                return QColor(249, 226, 175, 35)
            return None

        if role == Qt.ToolTipRole:
            if col in (5, 6):
                parts = []
                if entry.command:
                    parts.append(f"Command: {entry.command}")
                if entry.exec_args:
                    parts.append(f"Args: {' '.join(entry.exec_args)}")
                if col == 6:
                    parts.append(f"Path: {entry.file_path}")
                return "\n".join(parts) if parts else None
            return None

        if role == Qt.FontRole:
            if col == 0:
                font = QFont()
                font.setBold(True)
                font.setPointSize(14)
                return font

        if role == Qt.UserRole:
            return entry

        return None

    def headerData(self, section: int, orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def set_entries(self, entries: list[AutostartEntry]):
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()

    def add_entry(self, entry: AutostartEntry):
        row = len(self._entries)
        self.beginInsertRows(QModelIndex(), row, row)
        self._entries.append(entry)
        self.endInsertRows()

    def entry_at(self, row: int) -> AutostartEntry | None:
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None

    def get_all_entries(self) -> list[AutostartEntry]:
        return list(self._entries)


def _parse_search_query(query: str) -> list[tuple[str | None, str]]:
    parts = re.findall(r'(\w+):"([^"]*)"|(\w+):(\S+)|"([^"]*)"|(\S+)', query)
    tokens = []
    for m in parts:
        if m[0] and m[1]:
            tokens.append((m[0].lower(), m[1]))
        elif m[2] and m[3]:
            tokens.append((m[2].lower(), m[3]))
        elif m[4]:
            tokens.append((None, m[4]))
        elif m[5]:
            tokens.append((None, m[5]))
    return tokens


class EntryFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_category: str | None = None
        self._filter_enabled_only: bool = False
        self._filter_scope: str | None = None
        self._filter_tag: str | None = None
        self._filter_text: str = ""

    def set_category_filter(self, category: str | None):
        self._filter_category = category
        self.invalidate()

    def set_enabled_only(self, enabled: bool):
        self._filter_enabled_only = enabled
        self.invalidate()

    def set_scope_filter(self, scope: str | None):
        self._filter_scope = scope
        self.invalidate()

    def set_tag_filter(self, tag: str | None):
        self._filter_tag = tag
        self.invalidate()

    def set_search_text(self, text: str):
        self._filter_text = text
        self.invalidate()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if not model:
            return True
        index = model.index(source_row, 0, source_parent)
        entry: AutostartEntry | None = model.data(index, Qt.UserRole)
        if not entry:
            return True

        if self._filter_category and entry.category != self._filter_category:
            return False
        if self._filter_enabled_only and not entry.enabled:
            return False
        if self._filter_scope and entry.scope != self._filter_scope:
            return False
        if self._filter_tag and self._filter_tag not in entry.tags:
            return False

        if not self._filter_text:
            return True

        tokens = _parse_search_query(self._filter_text)
        if not tokens:
            return True

        searchable_all = (
            f"{entry.name} {entry.description or ''} {entry.command or ''} "
            f"{entry.file_path} {entry.category} {entry.user or ''} "
            f"{entry.owner or ''} {entry.scope} {' '.join(entry.tags)}"
        ).lower()

        field_map = {
            "name": entry.name.lower(),
            "category": entry.category.lower(),
            "user": (entry.user or "").lower(),
            "owner": (entry.owner or "").lower(),
            "scope": entry.scope.lower(),
            "command": (entry.command or "").lower(),
            "path": entry.file_path.lower(),
            "tag": " ".join(entry.tags).lower(),
            "tags": " ".join(entry.tags).lower(),
            "description": (entry.description or "").lower(),
        }

        for key, value in tokens:
            val_lower = value.lower()

            if key == "enabled":
                if val_lower in ("true", "1", "yes", "on"):
                    if not entry.enabled:
                        return False
                elif val_lower in ("false", "0", "no", "off"):
                    if entry.enabled:
                        return False
                else:
                    return False
                continue

            if key == "disabled":
                if val_lower in ("true", "1", "yes", "on"):
                    if entry.enabled:
                        return False
                elif val_lower in ("false", "0", "no", "off"):
                    if not entry.enabled:
                        return False
                else:
                    return False
                continue

            if key and key in _VALID_KEYS:
                if key not in field_map:
                    return False
                if val_lower not in field_map[key]:
                    return False
            else:
                if val_lower not in searchable_all:
                    return False

        return True
