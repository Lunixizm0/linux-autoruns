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
pip install linux-autoruns
# veya
pipx install linux-autoruns
```

## Çalıştırma

```bash
linux-autoruns               # root değilse sudo dialogu açar
sudo linux-autoruns          # root ile doğrudan başlat
```

## Geliştirme

Geliştirme ortamı için uv kullanılır:

```bash
git clone https://github.com/Lunixizm0/linux-autoruns.git
cd linux-autoruns
uv sync                      # ortamı kur
uv run linux-autoruns        # uygulamayı çalıştır
```

### Testler

```bash
uv run pytest tests/ -v
```

### Paketleme

```bash
uv run python -m build       # sdist + wheel oluşturur
```

## Teknoloji

- Python 3.14
- PySide6 6.11+ (Qt6 GUI)
- hatchling (build backend)
- uv (geliştirme ortamı)
- pytest (test framework)
