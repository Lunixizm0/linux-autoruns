from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from .gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Linux Autoruns")
    app.setApplicationVersion("1.0.0")
    if os.geteuid() != 0:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Root Yetkisi Gerekli")
        msg.setText("Bu uygulama tüm sistemi taramak için root yetkisi ile çalışmalıdır.")
        msg.setInformativeText(
            "Bazı scannerlar erişilemeyen dosyaları atlayacaktır.\n\n"
            "Tam tarama için:\n"
            "  sudo uv run linux-autoruns"
        )
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ret = msg.exec()
        if ret == QMessageBox.Cancel:
            sys.exit(0)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
