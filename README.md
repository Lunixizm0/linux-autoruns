# linux-autoruns

Windows Autoruns equivalent for Linux. Scans all autostart entry points on your system and lists them in a PySide6 GUI.

## Features

- 16 scanners: XDG Autostart, Systemd, SysVinit, Cron, Shell Profile, X11, Desktop Environment (GNOME, KDE, XFCE, Sway, Hyprland, Cinnamon, MATE, LXQt, COSMIC), Udev, D-Bus, Display Manager, Kernel (sysctl), Network Services (NGINX/Apache/SSH), PAM, tmpfiles.d, inetd/xinetd, GRUB
- Graphical user interface
- Category-based filtering and search
- Detail popup (right-click Inspect Details)
- JSON and CSV export
- Edit mode (enable/disable toggle)
- Settings persistence (window size)
- Automatic restart with root privileges (sudo)

## Installation

```bash
pip install linux-autoruns
# or
pipx install linux-autoruns
```

## Usage

```bash
linux-autoruns               # prompts for sudo if not root
sudo linux-autoruns          # runs directly with root
```

## Development

Development environment uses uv:

```bash
git clone https://github.com/Lunixizm0/linux-autoruns.git
cd linux-autoruns
uv sync                      # set up environment
uv run linux-autoruns        # run the app
```

### Testing

```bash
uv run pytest tests/ -v
```

### Building

```bash
uv run python -m build       # creates sdist + wheel
```

## Tech Stack

- Python 3.14
- PySide6 6.11+ (Qt6 GUI)
- hatchling (build backend)
- uv (development environment)
- pytest (test framework)
