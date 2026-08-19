# linux-autoruns

Sysinternals Autoruns'un Linux alternatifi. Sisteminizdeki tüm otomatik başlama noktarını tarar ve PySide6 GUI'de listeler.

## Özellikler

- 16 scanner: XDG Autostart, Systemd, SysVinit, Cron, Shell Profile, X11, Desktop Environment (GNOME, KDE, XFCE, Sway, Hyprland, Cinnamon, MATE, LXQt, COSMIC), Udev, D-Bus, Display Manager, Kernel (sysctl), Network Services (NGINX/Apache/SSH), PAM, tmpfiles.d, inetd/xinetd, GRUB
- Grafik Arayüzü
- Kategori bazlı filtreleme ve arama
- Detay popup (sağ tık Inspect Details)
- JSON ve CSV export
- Düzenleme modu (enable/disable toggle)
- Ayarların hatırlanması (pencere boyutu)
- Root yetkisi ile otomatik yeniden başlatma (sudo)

## Kurulum

```bash
# uv ile
uv sync

# bağımlılık ekle
uv add PySide6
```

## Çalıştırma

```bash
uv run linux-autoruns          # root değilse sudo dialogu açar
sudo uv run linux-autoruns     # root ile doğrudan başlat
```

## Testler

```bash
uv add --optional test pytest
uv run pytest tests/ -v
```

## Teknoloji

- Python 3.14
- PySide6 6.11+ (Qt6 GUI)
- uv (paket yönetimi)
- pytest (test framework)
