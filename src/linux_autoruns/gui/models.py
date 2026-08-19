from __future__ import annotations

from PySide6.QtCore import (QAbstractTableModel, QModelIndex,
                            QSortFilterProxyModel, Qt)
from PySide6.QtGui import QColor

from .theme import CATPPUCCIN_MOCHA
from ..models import AutostartEntry


class EntryTableModel(QAbstractTableModel):
    HEADERS = ["+", "Name", "Category", "User", "Description", "Modified"]
    _FIELD_MAP = {
        0: "enabled",
        1: "name",
        2: "category",
        3: "user",
        4: "description",
        5: "last_modified",
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
            field = self._FIELD_MAP.get(col)
            if field:
                val = getattr(entry, field, None)
                if val is None:
                    return ""
                return str(val)
            return ""
        if role == Qt.TextAlignmentRole:
            if col == 0:
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        if role == Qt.ForegroundRole:
            if col == 0:
                color = CATPPUCCIN_MOCHA["green"] if entry.enabled else CATPPUCCIN_MOCHA["red"]
                return QColor(color)
            if col == 1:
                return QColor(CATPPUCCIN_MOCHA["blue"])
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


class EntryFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_category: str | None = None
        self._filter_enabled_only: bool = False

    def set_category_filter(self, category: str | None):
        self._filter_category = category
        self.invalidateFilter()

    def set_enabled_only(self, enabled: bool):
        self._filter_enabled_only = enabled
        self.invalidateFilter()

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
        filter_str = self.filterRegularExpression().pattern()
        if filter_str:
            searchable = f"{entry.name} {entry.description or ''} {entry.command or ''} {entry.file_path}".lower()
            if filter_str.lower() not in searchable:
                return False
        return True
