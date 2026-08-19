from __future__ import annotations

import os
import shutil
import subprocess
import sys

from PySide6.QtWidgets import (QApplication, QInputDialog, QLineEdit,
                               QMessageBox)


def _is_root() -> bool:
    return os.geteuid() == 0


def _prompt_password_qt() -> str | None:
    password, ok = QInputDialog.getText(
        None,
        "Root Yetkisi",
        "Şifrenizi girin:",
        QLineEdit.EchoMode.Password,
    )
    if ok and password:
        return password
    return None


def _try_relaunch() -> bool:
    exe = shutil.which("linux-autoruns")
    if not exe:
        exe = sys.executable

    password = _prompt_password_qt()
    if not password:
        return False
    try:
        proc = subprocess.Popen(
            ["sudo", "-S", exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc.communicate(input=(password + "\n").encode(), timeout=30)
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
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
        btn_relaunch = msg.addButton("Evet (sudo)", QMessageBox.AcceptRole)
        btn_continue = msg.addButton("Hayır (devam et)", QMessageBox.RejectRole)
        msg.setDefaultButton(btn_relaunch)
        msg.exec()
        if msg.clickedButton() == btn_relaunch:
            if _try_relaunch():
                sys.exit(0)
            msg2 = QMessageBox()
            msg2.setIcon(QMessageBox.Critical)
            msg2.setWindowTitle("Hata")
            msg2.setText("sudo ile yeniden başlatılamadı.")
            msg2.setInformativeText("Terminalden çalıştırın:\n\n  sudo linux-autoruns")
            msg2.exec()
    from .gui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
