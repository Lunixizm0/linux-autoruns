from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox


def _is_root() -> bool:
    return os.geteuid() == 0


def _find_askpass() -> str | None:
    wrapper = Path(__file__).parent / "askpass.sh"
    if wrapper.exists():
        return str(wrapper)
    for name in ["zenity", "kdialog", "ssh-askpass"]:
        path = shutil.which(name)
        if path:
            return path
    return None


def _try_relaunch_with_sudo() -> bool:
    exe = shutil.which("linux-autoruns")
    if not exe:
        exe = sys.executable
    askpass = _find_askpass()
    env = os.environ.copy()
    if askpass:
        env["SUDO_ASKPASS"] = askpass
    env["DISPLAY"] = os.environ.get("DISPLAY", ":0")
    env["XAUTHORITY"] = os.environ.get("XAUTHORITY", os.path.expanduser("~/.Xauthority"))
    try:
        proc = subprocess.Popen(["sudo", "-A", exe], env=env)
        proc.wait()
        return proc.returncode == 0
    except FileNotFoundError:
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
            if _try_relaunch_with_sudo():
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
