from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

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
    return sys.executable


def _find_askpass_helper() -> str | None:
    for name in ["zenity", "kdialog", "ssh-askpass", "ksshaskpass",
                  "lxqt-sudo", "gnome-ssh-askpass", "x11-askpass"]:
        path = shutil.which(name)
        if path:
            return path
    return None


def _create_askpass_wrapper(helper: str) -> str:
    display = os.environ.get("DISPLAY", ":0")
    xauthority = os.environ.get("XAUTHORITY", os.path.expanduser("~/.Xauthority"))
    helper_name = Path(helper).name

    if helper_name in ("zenity",):
        run_cmd = f'exec "{helper}" --password --title="Password"'
    elif helper_name in ("kdialog",):
        run_cmd = f'exec "{helper}" --password "Enter your password:"'
    else:
        run_cmd = f'exec "{helper}" "$@"'

    content = f"""#!/bin/bash
export DISPLAY="{display}"
export XAUTHORITY="{xauthority}"
{run_cmd}
"""
    shm_dir = Path("/dev/shm")
    if not shm_dir.is_dir():
        shm_dir = Path(tempfile.gettempdir())

    fd, wrapper_path = tempfile.mkstemp(
        prefix=".askpass_",
        suffix=".sh",
        dir=str(shm_dir),
    )
    os.close(fd)
    Path(wrapper_path).write_text(content)
    os.chmod(wrapper_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    return wrapper_path


def _try_relaunch() -> bool:
    exe = _find_executable()
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

    helper = _find_askpass_helper()
    wrapper = None
    if helper:
        wrapper = _create_askpass_wrapper(helper)
        try:
            env["SUDO_ASKPASS"] = wrapper
            proc = subprocess.Popen(
                [sudo_exe, "-A", exe],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            _, stderr = proc.communicate(timeout=30)
            if proc.returncode == 0:
                return True
            if b"command not found" in stderr.lower() or b"not found" in stderr.lower():
                proc2 = subprocess.Popen(
                    [sudo_exe, "-A", sys.executable, "-m", "linux_autoruns"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                proc2.communicate(timeout=30)
                if proc2.returncode == 0:
                    return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        finally:
            if wrapper:
                try:
                    os.unlink(wrapper)
                except OSError:
                    pass

    password = _prompt_password_qt()
    if not password:
        return False
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
        if b"command not found" in stderr.lower() or b"not found" in stderr.lower():
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
