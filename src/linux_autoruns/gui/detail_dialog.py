from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGroupBox,
                               QLabel, QPlainTextEdit, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from ..gui.theme import DARK_THEME_QSS
from ..models import AutostartEntry


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
        container.setStyleSheet("background-color: #1e1e2e;")
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        self._add_section(layout, "Genel Bilgiler", self._general_fields(entry))
        if entry.command:
            self._add_section(layout, "Komut", {"Command": entry.command})
        if entry.exec_args:
            self._add_section(layout, "Argümanlar", {"Args": " ".join(entry.exec_args)})
        if entry.tags:
            self._add_section(layout, "Etiketler", {"Tags": ", ".join(entry.tags)})
        if entry.details:
            detail_items = {}
            for k, v in entry.details.items():
                if isinstance(v, list):
                    detail_items[k] = ", ".join(str(i) for i in v)
                else:
                    detail_items[k] = str(v)
            self._add_section(layout, "Detaylar", detail_items)
        if entry.file_path:
            content = self._read_raw_content(entry.file_path)
            if content:
                group = QGroupBox("Ham İçerik")
                vbox = QVBoxLayout()
                text_edit = QPlainTextEdit()
                text_edit.setPlainText(content)
                text_edit.setReadOnly(True)
                text_edit.setMaximumHeight(300)
                mono = QFont("monospace")
                mono.setStyleHint(QFont.Monospace)
                text_edit.setFont(mono)
                copy_btn = QPushButton("Kopyala")
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
        scroll.setStyleSheet("background-color: #1e1e2e;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _general_fields(self, entry: AutostartEntry) -> dict:
        fields = {}
        fields["Kategori"] = entry.category
        fields["Dosya"] = entry.file_path
        fields["Ad"] = entry.name
        fields["Durum"] = "✓ Aktif" if entry.enabled else "✗ Pasif"
        if entry.user:
            fields["Kullanıcı"] = entry.user
        fields["Scope"] = entry.scope
        if entry.description:
            fields["Tanım"] = entry.description
        if entry.comment:
            fields["Not"] = entry.comment
        if entry.last_modified:
            fields["Değişim"] = entry.last_modified
        if entry.file_size is not None:
            size = entry.file_size
            if size > 1024:
                fields["Boyut"] = f"{size / 1024:.1f} KB"
            else:
                fields["Boyut"] = f"{size} B"
        if entry.file_permissions:
            fields["İzinler"] = entry.file_permissions
        if entry.owner:
            fields["Sahip"] = entry.owner
        return fields

    def _add_section(self, layout: QVBoxLayout, title: str, items: dict):
        group = QGroupBox(title)
        vbox = QVBoxLayout()
        for key, value in items.items():
            lbl_key = QLabel(f"{key}:")
            lbl_val = QLabel(str(value))
            lbl_val.setWordWrap(True)
            lbl_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            btn = QPushButton("Kopyala")
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
            from pathlib import Path
            return Path(path).read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return None
