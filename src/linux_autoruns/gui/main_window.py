from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QMainWindow, QMenu, QMessageBox, QProgressBar,
                               QPushButton, QSplitter, QStatusBar, QTableView,
                               QToolButton, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

from ..models import AutostartEntry
from ..scanners import SCANNERS
from .detail_dialog import DetailDialog
from .models import EntryFilterProxy, EntryTableModel
from .theme import CATPPUCCIN_MOCHA, DARK_THEME_QSS
from .worker import ScanWorker

_SEARCH_HISTORY_KEY = "search_history"
_MAX_HISTORY = 20


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._settings = QSettings("linux-autoruns", "linux-autoruns")
        self.setWindowTitle("Linux Autoruns")
        self.setMinimumSize(1000, 600)
        self._restore_geometry()
        self._all_entries: list[AutostartEntry] = []
        self._worker: ScanWorker | None = None
        self._edit_mode = False
        self._selected_category: str | None = None
        self._error_count = 0
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

    def _restore_geometry(self):
        geom = self._settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)
        else:
            self.resize(1200, 700)

    def closeEvent(self, event):
        self._settings.setValue("geometry", self.saveGeometry())
        self._save_column_widths()
        self._save_search_history()
        super().closeEvent(event)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        toolbar = self._create_toolbar()
        main_layout.addLayout(toolbar)
        filter_bar = self._create_filter_bar()
        main_layout.addLayout(filter_bar)
        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximumHeight(4)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setValue(0)
        main_layout.addWidget(self._progress_bar)
        splitter = QSplitter(Qt.Horizontal)
        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("Categories")
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.AscendingOrder)
        self._tree.itemClicked.connect(self._on_category_clicked)
        self._tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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
        self._table.setMouseTracking(True)
        header = self._table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
        self._configure_table_columns()
        header.customContextMenuRequested.connect(self._on_header_context_menu)
        splitter.addWidget(self._table)
        splitter.setSizes([190, 1000])
        main_layout.addWidget(splitter)
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Scan not started")
        quit_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        quit_shortcut.activated.connect(self.close)

    def _configure_table_columns(self):
        header = self._table.horizontalHeader()
        stretch_cols = {1, 3, 5}
        content_cols = {0, 2, 4, 6, 7, 8, 9}
        for col in range(header.count()):
            if col in stretch_cols:
                header.setSectionResizeMode(col, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        saved_widths = self._settings.value("column_widths")
        if saved_widths:
            for col, width in saved_widths.items():
                try:
                    header.resizeSection(int(col), int(width))
                except (ValueError, TypeError):
                    pass

    def _save_column_widths(self):
        header = self._table.horizontalHeader()
        widths = {}
        for col in range(header.count()):
            if header.sectionResizeMode(col) == QHeaderView.Interactive:
                widths[col] = header.sectionSize(col)
        self._settings.setValue("column_widths", widths)

    def _on_header_context_menu(self, pos):
        header = self._table.horizontalHeader()
        menu = QMenu(self)
        from .models import EntryTableModel
        headers = EntryTableModel.HEADERS
        for col in range(header.count()):
            action = menu.addAction(headers[col])
            action.setCheckable(True)
            action.setChecked(not header.isSectionHidden(col))
            action.triggered.connect(
                lambda checked, c=col: self._toggle_column(c, checked)
            )
        menu.exec(header.mapToGlobal(pos))

    def _toggle_column(self, col: int, visible: bool):
        self._table.setColumnHidden(col, not visible)

    def _create_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 8, 8, 8)
        toolbar.setSpacing(8)
        lbl = QLabel("Search")
        lbl.setStyleSheet(f"color: {CATPPUCCIN_MOCHA['blue']}; font-size: 16px;")
        toolbar.addWidget(lbl)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search... (key:value, name:ssh, tag:boot)")
        self._search.setFixedWidth(320)
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search)
        self._search.returnPressed.connect(self._on_search_commit)
        self._search.setCompleter(None)
        toolbar.addWidget(self._search)
        self._history_btn = QToolButton()
        self._history_btn.setText("History")
        self._history_btn.setPopupMode(QToolButton.InstantPopup)
        self._history_menu = QMenu(self._history_btn)
        self._history_btn.setMenu(self._history_menu)
        self._history_btn.setStyleSheet(
            f"QToolButton {{ color: {CATPPUCCIN_MOCHA['overlay1']}; "
            f"font-size: 11px; padding: 2px 6px; border: none; }}"
        )
        toolbar.addWidget(self._history_btn)
        self._enabled_only = QCheckBox("Enabled only")
        self._enabled_only.stateChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._enabled_only)
        self._edit_mode_cb = QCheckBox("Edit Mode")
        self._edit_mode_cb.stateChanged.connect(self._on_edit_mode_changed)
        toolbar.addWidget(self._edit_mode_cb)
        toolbar.addStretch()
        self._result_label = QLabel("")
        self._result_label.setStyleSheet(
            f"color: {CATPPUCCIN_MOCHA['overlay1']}; font-size: 12px;"
        )
        toolbar.addWidget(self._result_label)
        self._scan_btn = QPushButton("Scan")
        self._scan_btn.clicked.connect(self._start_scan)
        toolbar.addWidget(self._scan_btn)
        self._export_json_btn = QPushButton("Export JSON")
        self._export_json_btn.clicked.connect(self._export_json)
        self._export_json_btn.setEnabled(False)
        toolbar.addWidget(self._export_json_btn)
        self._export_csv_btn = QPushButton("Export CSV")
        self._export_csv_btn.clicked.connect(self._export_csv)
        self._export_csv_btn.setEnabled(False)
        toolbar.addWidget(self._export_csv_btn)
        return toolbar

    def _create_filter_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setContentsMargins(8, 0, 8, 4)
        bar.setSpacing(4)
        lbl = QLabel("Scope:")
        lbl.setStyleSheet(f"color: {CATPPUCCIN_MOCHA['overlay1']}; font-size: 11px;")
        bar.addWidget(lbl)
        self._scope_combo = QComboBox()
        self._scope_combo.addItem("All")
        self._scope_combo.addItem("System")
        self._scope_combo.addItem("User")
        self._scope_combo.setFixedWidth(80)
        self._scope_combo.currentTextChanged.connect(self._on_scope_changed)
        bar.addWidget(self._scope_combo)
        bar.addSpacing(8)
        lbl2 = QLabel("Tag:")
        lbl2.setStyleSheet(f"color: {CATPPUCCIN_MOCHA['overlay1']}; font-size: 11px;")
        bar.addWidget(lbl2)
        self._tag_combo = QComboBox()
        self._tag_combo.addItem("All")
        self._tag_combo.setFixedWidth(120)
        self._tag_combo.currentTextChanged.connect(self._on_tag_changed)
        bar.addWidget(self._tag_combo)
        bar.addSpacing(8)
        for label, query in [
            ("All", ""),
            ("Enabled", "enabled:true"),
            ("Disabled", "enabled:false"),
            ("Boot", "tag:boot"),
            ("Login", "tag:login"),
            ("Timer", "tag:timer"),
            ("Session", "tag:session"),
        ]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            btn.setStyleSheet(
                f"QPushButton {{ font-size: 11px; padding: 2px 8px; "
                f"border: 1px solid {CATPPUCCIN_MOCHA['surface1']}; "
                f"border-radius: 4px; color: {CATPPUCCIN_MOCHA['text']}; "
                f"background: {CATPPUCCIN_MOCHA['surface0']}; }}"
                f"QPushButton:checked {{ background: {CATPPUCCIN_MOCHA['blue']}; "
                f"color: {CATPPUCCIN_MOCHA['base']}; border-color: {CATPPUCCIN_MOCHA['blue']}; }}"
            )
            btn.clicked.connect(lambda checked, q=query, b=btn: self._on_quick_filter(q, b))
            bar.addWidget(btn)
        bar.addStretch()
        self._filter_bar = bar
        return bar

    def _apply_theme(self):
        self.setStyleSheet(DARK_THEME_QSS)

    def _on_edit_mode_changed(self, state):
        self._edit_mode = state == Qt.Checked.value

    def _start_scan(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._scan_btn.setText("Scan")
            self._progress_bar.setValue(0)
            return
        self._all_entries.clear()
        self._selected_category = None
        self._error_count = 0
        self._model.set_entries([])
        self._tree.clear()
        self._scan_btn.setText("Stop")
        self._export_json_btn.setEnabled(False)
        self._export_csv_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._worker = ScanWorker(SCANNERS, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.entries_batch.connect(self._on_entries_batch)
        self._worker.scan_complete.connect(self._on_scan_complete)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, category: str, percent: int):
        self._progress_bar.setValue(percent)
        self._status_bar.showMessage(f"Scanning: {category} ({percent}%)")

    def _on_entries_batch(self, entries: list):
        self._all_entries.extend(entries)
        for entry in entries:
            self._model.add_entry(entry)

    def _on_scan_complete(self, entries: list):
        self._all_entries = entries
        self._model.set_entries(entries)
        self._scan_btn.setText("Scan")
        self._export_json_btn.setEnabled(True)
        self._export_csv_btn.setEnabled(True)
        self._progress_bar.setValue(100)
        self._rebuild_tree()
        self._rebuild_tag_list()
        self._update_result_count()
        total = len(entries)
        enabled = sum(1 for e in entries if e.enabled)
        cats = len(set(e.category for e in entries))
        msg = f"Completed: {total} entries ({enabled} active) - {cats} categories"
        if self._error_count:
            msg += f" ({self._error_count} errors)"
        self._status_bar.showMessage(msg)
        scopes = {e.scope for e in entries}
        self._table.setColumnHidden(6, len(scopes) <= 1)
        owners = {e.owner for e in entries if e.owner}
        self._table.setColumnHidden(9, len(owners) <= 1)

    def _on_error(self, msg: str):
        self._error_count += 1
        self._status_bar.showMessage(f"Error ({self._error_count}): {msg[:80]}")

    def _rebuild_tree(self):
        self._tree.clear()
        root = QTreeWidgetItem(self._tree)
        root.setText(0, f"All ({len(self._all_entries)})")
        root.setData(0, Qt.UserRole, len(self._all_entries))
        counts: dict[str, int] = {}
        for entry in self._all_entries:
            counts[entry.category] = counts.get(entry.category, 0) + 1
        for cat in sorted(counts):
            item = QTreeWidgetItem(self._tree)
            text = f"{cat} ({counts[cat]})"
            item.setText(0, text)
            item.setData(0, Qt.UserRole, counts[cat])
        self._tree.setFixedWidth(190)

    def _rebuild_tag_list(self):
        tags: set[str] = set()
        for entry in self._all_entries:
            tags.update(entry.tags)
        current = self._tag_combo.currentText()
        self._tag_combo.blockSignals(True)
        self._tag_combo.clear()
        self._tag_combo.addItem("All")
        for tag in sorted(tags):
            self._tag_combo.addItem(tag)
        idx = self._tag_combo.findText(current)
        if idx >= 0:
            self._tag_combo.setCurrentIndex(idx)
        self._tag_combo.blockSignals(False)

    def _update_result_count(self):
        total = len(self._all_entries)
        visible = self._proxy.rowCount()
        if visible == total:
            self._result_label.setText(f"{total} entries")
        else:
            self._result_label.setText(f"{visible} / {total} entries")

    def _on_category_clicked(self, item: QTreeWidgetItem, column: int):
        text = item.text(0)
        if text.startswith("All"):
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
        scope = self._scope_combo.currentText()
        self._proxy.set_scope_filter(None if scope == "All" else scope.lower())
        tag = self._tag_combo.currentText()
        self._proxy.set_tag_filter(None if tag == "All" else tag)
        self._proxy.set_search_text(self._search.text())
        self._update_result_count()

    def _on_search(self, text: str):
        self._search_debounce.start()

    def _on_search_commit(self):
        text = self._search.text().strip()
        if text:
            self._add_to_history(text)
        self._apply_filters()

    def _add_to_history(self, text: str):
        history = self._settings.value(_SEARCH_HISTORY_KEY, []) or []
        if text in history:
            history.remove(text)
        history.insert(0, text)
        history = history[:_MAX_HISTORY]
        self._settings.setValue(_SEARCH_HISTORY_KEY, history)
        self._refresh_history_menu()

    def _save_search_history(self):
        pass

    def _refresh_history_menu(self):
        self._history_menu.clear()
        history = self._settings.value(_SEARCH_HISTORY_KEY, []) or []
        if not history:
            self._history_menu.addAction("(empty)")
            return
        for text in history:
            action = self._history_menu.addAction(text)
            action.triggered.connect(lambda checked, t=text: self._search.setText(t))
        self._history_menu.addSeparator()
        clear_action = self._history_menu.addAction("Clear history")
        clear_action.triggered.connect(self._clear_history)

    def _clear_history(self):
        self._settings.setValue(_SEARCH_HISTORY_KEY, [])
        self._refresh_history_menu()

    def _on_scope_changed(self, text: str):
        self._apply_filters()

    def _on_tag_changed(self, text: str):
        self._apply_filters()

    def _on_quick_filter(self, query: str, btn: QPushButton):
        for i in range(self._filter_bar.count()):
            w = self._filter_bar.itemAt(i).widget()
            if isinstance(w, QPushButton) and w.isCheckable() and w != btn:
                w.setChecked(False)
        if btn.isChecked():
            self._search.setText(query)
        else:
            self._search.setText("")
        self._apply_filters()

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
        if self._edit_mode:
            menu.addSeparator()
            toggle_action = menu.addAction(
                "Disable" if entry.enabled else "Enable"
            )
        else:
            toggle_action = None
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
        elif toggle_action and action == toggle_action:
            entry.enabled = not entry.enabled
            self._model.set_entries(list(self._model.get_all_entries()))

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
            self, "Save as JSON", "autoruns_export.json", "JSON (*.json)"
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
            self._status_bar.showMessage(f"Exported: {path}")
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not save JSON: {e}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save as CSV", "autoruns_export.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Enabled", "Name", "Category", "Description",
                                 "Command", "Path", "Scope", "Permissions",
                                 "Size", "Owner", "Tags"])
                for entry in self._all_entries:
                    size_str = ""
                    if entry.file_size is not None:
                        if entry.file_size < 1024:
                            size_str = f"{entry.file_size} B"
                        elif entry.file_size < 1024 * 1024:
                            size_str = f"{entry.file_size / 1024:.1f} KB"
                        else:
                            size_str = f"{entry.file_size / (1024 * 1024):.1f} MB"
                    writer.writerow([
                        "+" if entry.enabled else "-",
                        entry.name,
                        entry.category,
                        entry.description or "",
                        entry.command or "",
                        entry.file_path,
                        entry.scope,
                        entry.file_permissions or "",
                        size_str,
                        entry.owner or "",
                        ",".join(entry.tags),
                    ])
            self._status_bar.showMessage(f"Exported: {path}")
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not save CSV: {e}")
