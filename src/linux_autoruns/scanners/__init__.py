from .xdg import XDGScanner
from .systemd import SystemdScanner
from .init import InitScanner
from .cron import CronScanner
from .shell import ShellScanner
from .x11 import X11Scanner
from .desktop_env import DesktopEnvScanner
from .udev import UdevScanner
from .dbus import DbusScanner
from .display_manager import DisplayManagerScanner
from .kernel import KernelScanner
from .network_services import NetworkServicesScanner
from .pam import PAMScanner
from .tmpfiles import TmpfilesScanner
from .inetd import InetdScanner
from .grub import GrubScanner

SCANNERS = [
    XDGScanner,
    SystemdScanner,
    InitScanner,
    CronScanner,
    ShellScanner,
    X11Scanner,
    DesktopEnvScanner,
    UdevScanner,
    DbusScanner,
    DisplayManagerScanner,
    KernelScanner,
    NetworkServicesScanner,
    PAMScanner,
    TmpfilesScanner,
    InetdScanner,
    GrubScanner,
]
