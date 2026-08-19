from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal

from ..models import AutostartEntry
from ..scanner import BaseScanner

_BATCH_SIZE = 32


class ScanWorker(QThread):
    progress = Signal(str, int)
    entries_batch = Signal(list)
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
                all_entries.extend(entries)
                batch = []
                for entry in entries:
                    if self._cancelled:
                        break
                    batch.append(entry)
                    if len(batch) >= _BATCH_SIZE:
                        self.entries_batch.emit(batch)
                        batch = []
                if batch:
                    self.entries_batch.emit(batch)
            except Exception:
                self.error.emit(f"{scanner.name}: {traceback.format_exc()}")
        self.progress.emit("Completed", 100)
        self.scan_complete.emit(all_entries)
