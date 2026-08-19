from __future__ import annotations

import os
import shutil
import subprocess
import sys

from PySide6.QtWidgets import QApplication, QMessageBox


def _is_root() -> bool:
    return os.geteuid() == 0


def _try_relaunch_with_sudo() -> bool:
    exe = shutil.which("linux-autoruns")
    if not exe:
        try:
            import importlib.resources
            exe = sys.executable
        except Exception:
            exe = sys.executable
    for tool in ["pkexec", "sudo -A"]:
        try:
            cmd = tool.split() + [exe]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.wait()
            return True
        except FileNotFoundError:
            continue
    return False


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Linux Autoruns")
    app.setApplicationVersion("0.1.0")
    if not _is_root():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Root Yetkisi Gerekli")
        msg.setText("Bu uygulama tüm sistemi taramak için root yetkisi ile çalışmalıdır.")
        msg.setInformativeText(
            "Root olmadan bazı dosyalar erişilemez.\n\n"
            "Root ile yeniden başlatılsın mı?"
        )
        btn_relaunch = msg.addButton("Evet (pkexec/sudo)", QMessageBox.AcceptRole)
        btn_continue = msg.addButton("Hayır (devam et)", QMessageBox.RejectRole)
        msg.setDefaultButton(btn_relaunch)
        msg.exec()
        if msg.clickedButton() == btn_relaunch:
            _try_relaunch_with_sudo()
            sys.exit(0)
    from .gui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
