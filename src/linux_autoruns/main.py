from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import (QApplication, QMessageBox, QPushButton,
                                QSizePolicy)


def _is_root() -> bool:
    return os.geteuid() == 0


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Linux Autoruns")
    if not _is_root():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Root Access Required")
        msg.setText("This application requires root access to scan the entire system.")
        msg.setInformativeText(
            "Without root, some files cannot be accessed.\n\n"
            "Please restart with:\n\n  sudo linux-autoruns"
        )
        btn = msg.addButton("Continue Anyway", QMessageBox.RejectRole)
        msg.setDefaultButton(btn)
        msg.exec()
    from .gui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
