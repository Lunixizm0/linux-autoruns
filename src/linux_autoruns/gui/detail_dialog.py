from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QDialog, QGroupBox, QLabel,
                               QPlainTextEdit, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from ..gui.theme import CATPPUCCIN_MOCHA, DARK_THEME_QSS
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
                group.setStyleSheet(f"""
                    QGroupBox {{
                        color: {CATPPUCCIN_MOCHA['text']};
                        border: 1px solid {CATPPUCCIN_MOCHA['surface0']};
                        border-radius: 4px;
                        margin-top: 8px;
                        padding-top: 12px;
                        font-weight: bold;
                    }}
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        subcontrol-position: top left;
                        left: 8px;
                        padding: 0 4px;
                    }}
                """)
                vbox = QVBoxLayout()
                text_edit = QPlainTextEdit()
                text_edit.setPlainText(content)
                text_edit.setReadOnly(True)
                text_edit.setMaximumHeight(300)
                mono = QFont("monospace")
                mono.setStyleHint(QFont.Monospace)
                text_edit.setFont(mono)
                copy_btn = QPushButton("Kopyala")
                copy_btn.setFixedWidth(80)
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
        fields["Kategori"] = entry.category
        fields["Dosya"] = entry.file_path
        fields["Ad"] = entry.name
        fields["Durum"] = "+ Aktif" if entry.enabled else "- Pasif"
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
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {CATPPUCCIN_MOCHA['text']};
                border: 1px solid {CATPPUCCIN_MOCHA['surface0']};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 4px;
            }}
        """)
        vbox = QVBoxLayout()
        for key, value in items.items():
            row = QVBoxLayout()
            lbl_key = QLabel(f"{key}:")
            lbl_key.setStyleSheet(f"color: {CATPPUCCIN_MOCHA['subtext0']}; font-weight: normal;")
            lbl_val = QLabel(str(value))
            lbl_val.setWordWrap(True)
            lbl_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lbl_val.setStyleSheet(f"color: {CATPPUCCIN_MOCHA['text']};")
            row.addWidget(lbl_key)
            row.addWidget(lbl_val)
            btn = QPushButton("Kopyala")
            btn.setFixedWidth(70)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {CATPPUCCIN_MOCHA['surface0']};
                    color: {CATPPUCCIN_MOCHA['text']};
                    border: 1px solid {CATPPUCCIN_MOCHA['surface1']};
                    border-radius: 3px;
                    padding: 2px 8px;
                    font-size: 11px;
                }}
                QPushButton:hover {{ background-color: {CATPPUCCIN_MOCHA['surface1']}; }}
            """)
            btn.clicked.connect(lambda checked, v=str(value): QApplication.clipboard().setText(v))
            h = QVBoxLayout()
            top_row = QVBoxLayout()
            top_row.addWidget(lbl_key)
            top_row.addWidget(btn)
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
