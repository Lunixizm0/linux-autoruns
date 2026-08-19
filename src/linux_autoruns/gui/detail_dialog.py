from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QDialog, QGroupBox, QLabel,
                               QPlainTextEdit, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from ..models import AutostartEntry
from .theme import DARK_THEME_QSS


class DetailDialog(QDialog):
    def __init__(self, entry: AutostartEntry, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Entry Detail: {entry.name}")
        self.setMinimumSize(550, 500)
        self.setMaximumSize(700, 900)
        self.setStyleSheet(DARK_THEME_QSS)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        self._add_section(layout, "General Info", self._general_fields(entry))
        if entry.command:
            self._add_section(layout, "Command", {"Command": entry.command})
        if entry.exec_args:
            self._add_section(layout, "Arguments", {"Args": " ".join(entry.exec_args)})
        if entry.tags:
            self._add_section(layout, "Tags", {"Tags": ", ".join(entry.tags)})
        if entry.details:
            detail_items = {}
            for k, v in entry.details.items():
                if isinstance(v, list):
                    detail_items[k] = ", ".join(str(i) for i in v)
                else:
                    detail_items[k] = str(v)
            self._add_section(layout, "Details", detail_items)
        if entry.file_path:
            content = self._read_raw_content(entry.file_path)
            if content:
                group = QGroupBox("Raw Content")
                vbox = QVBoxLayout()
                text_edit = QPlainTextEdit()
                text_edit.setPlainText(content)
                text_edit.setReadOnly(True)
                text_edit.setMaximumHeight(300)
                mono = QFont("monospace")
                mono.setStyleHint(QFont.Monospace)
                text_edit.setFont(mono)
                copy_btn = QPushButton("Copy")
                copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(content))
                btn_row = QVBoxLayout()
                btn_row.addWidget(copy_btn)
                btn_row.addStretch()
                hbox = QVBoxLayout()
                hbox.addWidget(text_edit)
                hbox.addLayout(btn_row)
                vbox.addLayout(hbox)
                group.setLayout(vbox)
                layout.addWidget(group)
        layout.addStretch()
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _general_fields(self, entry: AutostartEntry) -> dict:
        fields = {}
        fields["Category"] = entry.category
        fields["File"] = entry.file_path
        fields["Name"] = entry.name
        fields["Status"] = "+ Enabled" if entry.enabled else "- Disabled"
        if entry.user:
            fields["User"] = entry.user
        fields["Scope"] = entry.scope
        if entry.description:
            fields["Description"] = entry.description
        if entry.comment:
            fields["Note"] = entry.comment
        if entry.last_modified:
            fields["Modified"] = entry.last_modified
        if entry.file_size is not None:
            size = entry.file_size
            if size > 1024:
                fields["Size"] = f"{size / 1024:.1f} KB"
            else:
                fields["Size"] = f"{size} B"
        if entry.file_permissions:
            fields["Permissions"] = entry.file_permissions
        if entry.owner:
            fields["Owner"] = entry.owner
        return fields

    def _add_section(self, layout: QVBoxLayout, title: str, items: dict):
        group = QGroupBox(title)
        vbox = QVBoxLayout()
        for key, value in items.items():
            lbl_key = QLabel(f"{key}:")
            lbl_val = QLabel(str(value))
            lbl_val.setWordWrap(True)
            lbl_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            btn = QPushButton("Copy")
            btn.clicked.connect(lambda checked, v=str(value): QApplication.clipboard().setText(v))
            top_row = QVBoxLayout()
            top_row.addWidget(lbl_key)
            top_row.addWidget(btn)
            h = QVBoxLayout()
            h.addLayout(top_row)
            h.addWidget(lbl_val)
            vbox.addLayout(h)
        group.setLayout(vbox)
        layout.addWidget(group)

    def _read_raw_content(self, path: str) -> str | None:
        try:
            return Path(path).read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return None
