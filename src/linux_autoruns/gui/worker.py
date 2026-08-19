from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal

from ..models import AutostartEntry
from ..scanner import BaseScanner


class ScanWorker(QThread):
    progress = Signal(str, int)
    entry_found = Signal(object)
    scan_complete = Signal(list)
    error = Signal(str)

    def __init__(self, scanners: list[type[BaseScanner]], parent=None):
        super().__init__(parent)
        self._scanners = scanners
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        all_entries: list[AutostartEntry] = []
        total = len(self._scanners)
        for i, scanner_cls in enumerate(self._scanners):
            if self._cancelled:
                break
            scanner = scanner_cls()
            self.progress.emit(scanner.name, int(i / total * 100))
            try:
                entries = scanner.scan()
                for entry in entries:
                    if self._cancelled:
                        break
                    all_entries.append(entry)
                    self.entry_found.emit(entry)
            except Exception:
                self.error.emit(f"{scanner.name}: {traceback.format_exc()}")
        self.progress.emit("Completed", 100)
        self.scan_complete.emit(all_entries)
