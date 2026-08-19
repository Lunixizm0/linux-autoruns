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
        "Root Access",
        "Enter your password:",
        QLineEdit.EchoMode.Password,
    )
    if ok and password:
        return password
    return None


def _find_executable() -> str:
    exe = shutil.which("linux-autoruns")
    if exe:
        return exe
    if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        return sys.executable
    return sys.executable


def _try_relaunch() -> bool:
    exe = _find_executable()

    password = _prompt_password_qt()
    if not password:
        return False

    sudo_exe = shutil.which("sudo")
    if not sudo_exe:
        return False

    env = os.environ.copy()
    home = os.path.expanduser("~")
    paths = env.get("PATH", "")
    for extra in [".local/bin", ".local/pipx/venvs/linux-autoruns/bin"]:
        p = os.path.join(home, extra)
        if p not in paths:
            paths = f"{p}:{paths}"
    env["PATH"] = paths

    try:
        proc = subprocess.Popen(
            [sudo_exe, "-S", exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=env,
        )
        _, stderr = proc.communicate(input=(password + "\n").encode(), timeout=30)
        if proc.returncode == 0:
            return True
        if b"command not found" in stderr.lower():
            proc2 = subprocess.Popen(
                [sudo_exe, "-S", sys.executable, "-m", "linux_autoruns"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )
            proc2.communicate(input=(password + "\n").encode(), timeout=30)
            return proc2.returncode == 0
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


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
            "Restart with root?"
        )
        btn_relaunch = msg.addButton("Yes (sudo)", QMessageBox.AcceptRole)
        btn_continue = msg.addButton("No (continue)", QMessageBox.RejectRole)
        msg.setDefaultButton(btn_relaunch)
        msg.exec()
        if msg.clickedButton() == btn_relaunch:
            if _try_relaunch():
                sys.exit(0)
            msg2 = QMessageBox()
            msg2.setIcon(QMessageBox.Critical)
            msg2.setWindowTitle("Error")
            msg2.setText("Could not restart with sudo.")
            msg2.setInformativeText("Run from terminal:\n\n  sudo linux-autoruns")
            msg2.exec()
    from .gui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
