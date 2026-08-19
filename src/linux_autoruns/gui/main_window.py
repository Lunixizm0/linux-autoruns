from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QCheckBox, QFileDialog,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QMainWindow, QMenu, QMessageBox, QPushButton,
                               QSplitter, QStatusBar, QTableView, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

from ..models import AutostartEntry
from ..scanners import SCANNERS
from .detail_dialog import DetailDialog
from .models import EntryTableModel, EntryFilterProxy
from .theme import CATPPUCCIN_MOCHA, DARK_THEME_QSS
from .worker import ScanWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux Autoruns")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 700)
        self._all_entries: list[AutostartEntry] = []
        self._worker: ScanWorker | None = None
        self._edit_mode = False
        self._selected_category: str | None = None
        self._model = EntryTableModel(self)
        self._proxy = EntryFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self._search_debounce = QTimer()
        self._search_debounce.setSingleShot(True)
        self._search_debounce.setInterval(150)
        self._search_debounce.timeout.connect(self._apply_filters)
        self._setup_ui()
        self._apply_theme()
        self._start_scan()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        toolbar = self._create_toolbar()
        main_layout.addLayout(toolbar)
        splitter = QSplitter(Qt.Horizontal)
        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("Kategoriler")
        self._tree.setMinimumWidth(200)
        self._tree.setMaximumWidth(350)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.AscendingOrder)
        self._tree.itemClicked.connect(self._on_category_clicked)
        splitter.addWidget(self._tree)
        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_inspect)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        splitter.addWidget(self._table)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Tarama başlatılmadı")
        quit_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        quit_shortcut.activated.connect(self.close)

    def _create_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 8, 8, 8)
        toolbar.setSpacing(8)
        lbl = QLabel("🔍")
        lbl.setStyleSheet(f"color: {CATPPUCCIN_MOCHA['blue']}; font-size: 16px;")
        toolbar.addWidget(lbl)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Ara... (isim, komut, dosya)")
        self._search.setFixedWidth(250)
        self._search.textChanged.connect(self._on_search)
        toolbar.addWidget(self._search)
        self._enabled_only = QCheckBox("Sadece aktif")
        self._enabled_only.stateChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._enabled_only)
        self._edit_mode_cb = QCheckBox("Düzenleme Modu")
        self._edit_mode_cb.stateChanged.connect(self._on_edit_mode_changed)
        toolbar.addWidget(self._edit_mode_cb)
        toolbar.addStretch()
        self._scan_btn = QPushButton("Scan")
        self._scan_btn.clicked.connect(self._start_scan)
        toolbar.addWidget(self._scan_btn)
        self._export_btn = QPushButton("Export JSON")
        self._export_btn.clicked.connect(self._export_json)
        self._export_btn.setEnabled(False)
        toolbar.addWidget(self._export_btn)
        return toolbar

    def _apply_theme(self):
        self.setStyleSheet(DARK_THEME_QSS)

    def _on_edit_mode_changed(self, state):
        self._edit_mode = state == Qt.Checked.value

    def _start_scan(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._scan_btn.setText("Scan")
            return
        self._all_entries.clear()
        self._selected_category = None
        self._model.set_entries([])
        self._tree.clear()
        self._add_tree_root()
        self._scan_btn.setText("Durdur")
        self._export_btn.setEnabled(False)
        self._worker = ScanWorker(SCANNERS, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.entry_found.connect(self._on_entry_found)
        self._worker.scan_complete.connect(self._on_scan_complete)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _add_tree_root(self):
        item = QTreeWidgetItem(self._tree)
        item.setText(0, "Tümü (0)")
        item.setData(0, Qt.UserRole, 0)

    def _on_progress(self, category: str, percent: int):
        self._status_bar.showMessage(f"Taranıyor: {category} ({percent}%)")

    def _on_entry_found(self, entry: AutostartEntry):
        self._all_entries.append(entry)
        self._model.add_entry(entry)
        self._update_tree_count(entry.category)

    def _on_scan_complete(self, entries: list):
        self._all_entries = entries
        self._model.set_entries(entries)
        self._scan_btn.setText("Scan")
        self._export_btn.setEnabled(True)
        total = len(entries)
        enabled = sum(1 for e in entries if e.enabled)
        cats = len(set(e.category for e in entries))
        self._status_bar.showMessage(f"Tamamlandı: {total} entry ({enabled} aktif) - {cats} kategori")
        has_user = any(e.user for e in entries)
        self._table.setColumnHidden(3, not has_user)
        self._update_tree_root_count()

    def _on_error(self, msg: str):
        self._status_bar.showMessage(f"Hata: {msg[:100]}")

    def _update_tree_root_count(self):
        if self._tree.topLevelItemCount() > 0:
            item = self._tree.topLevelItem(0)
            item.setText(0, f"Tümü ({len(self._all_entries)})")
            item.setData(0, Qt.UserRole, len(self._all_entries))

    def _update_tree_count(self, category: str):
        for i in range(1, self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item.text(0).startswith(category):
                count = item.data(0, Qt.UserRole) or 0
                count += 1
                item.setData(0, Qt.UserRole, count)
                item.setText(0, f"{category} ({count})")
                return
        item = QTreeWidgetItem(self._tree)
        item.setText(0, f"{category} (1)")
        item.setData(0, Qt.UserRole, 1)
        self._update_tree_root_count()

    def _on_category_clicked(self, item: QTreeWidgetItem, column: int):
        text = item.text(0)
        if text.startswith("Tümü"):
            self._selected_category = None
        else:
            category = text.rsplit(" (", 1)[0] if " (" in text else text
            if self._selected_category == category:
                self._selected_category = None
            else:
                self._selected_category = category
        self._apply_filters()

    def _apply_filters(self):
        self._proxy.set_category_filter(self._selected_category)
        self._proxy.set_enabled_only(self._enabled_only.isChecked())
        self._proxy.set_search_text(self._search.text())
        has_user = any(e.user for e in self._all_entries)
        self._table.setColumnHidden(3, not has_user)

    def _on_search(self, text: str):
        self._search_debounce.start()

    def _on_filter_changed(self):
        self._apply_filters()

    def _on_context_menu(self, pos):
        index = self._table.indexAt(pos)
        if not index.isValid():
            return
        source_index = self._proxy.mapToSource(index)
        entry: AutostartEntry | None = self._model.entry_at(source_index.row())
        if not entry:
            return
        menu = QMenu(self)
        copy_name = menu.addAction("Copy Name")
        copy_path = menu.addAction("Copy Path")
        copy_command = menu.addAction("Copy Command")
        copy_json = menu.addAction("Copy Full Details (JSON)")
        menu.addSeparator()
        inspect_action = menu.addAction("Inspect Details...")
        menu.addSeparator()
        open_location = menu.addAction("Open File Location")
        action = menu.exec(self._table.mapToGlobal(pos))
        if action == copy_name:
            QApplication.clipboard().setText(entry.name)
        elif action == copy_path:
            QApplication.clipboard().setText(entry.file_path)
        elif action == copy_command:
            QApplication.clipboard().setText(entry.command or "")
        elif action == copy_json:
            QApplication.clipboard().setText(json.dumps(entry.to_dict(), indent=2, ensure_ascii=False))
        elif action == inspect_action:
            self._open_detail(entry)
        elif action == open_location:
            dirpath = os.path.dirname(entry.file_path)
            if os.path.isdir(dirpath):
                subprocess.Popen(["xdg-open", dirpath])

    def _on_inspect(self, index):
        source_index = self._proxy.mapToSource(index)
        entry: AutostartEntry | None = self._model.entry_at(source_index.row())
        if entry:
            self._open_detail(entry)

    def _open_detail(self, entry: AutostartEntry):
        dialog = DetailDialog(entry, self)
        dialog.exec()

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "JSON olarak kaydet", "autoruns_export.json", "JSON (*.json)"
        )
        if not path:
            return
        data = {
            "scan_time": datetime.now(tz=timezone.utc).isoformat(),
            "hostname": os.uname().nodename,
            "entries": [e.to_dict() for e in self._all_entries],
            "summary": {
                "total": len(self._all_entries),
                "enabled": sum(1 for e in self._all_entries if e.enabled),
                "by_category": {},
            },
        }
        for entry in self._all_entries:
            cat = entry.category
            data["summary"]["by_category"][cat] = data["summary"]["by_category"].get(cat, 0) + 1
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._status_bar.showMessage(f"Dışa aktarıldı: {path}")
        except OSError as e:
            QMessageBox.critical(self, "Hata", f"JSON kaydedilemedi: {e}")
