from __future__ import annotations

from pathlib import Path

from linux_autoruns.scanners.systemd import SystemdScanner


def test_parse_unit_service(tmp_path):
    service_dir = tmp_path / "system"
    service_dir.mkdir()
    service_file = service_dir / "test.service"
    service_file.write_text(
        "[Unit]\n"
        "Description=Test Service\n"
        "After=network.target\n"
        "\n"
        "[Service]\n"
        "ExecStart=/usr/bin/test --arg1 --arg2\n"
        "Restart=on-failure\n"
        "Type=simple\n"
        "User=nobody\n"
        "\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )
    scanner = SystemdScanner()
    entry = scanner._parse_unit(str(service_file), "system")
    assert entry is not None
    assert entry.name == "test.service"
    assert entry.description == "Test Service"
    assert entry.command == "/usr/bin/test"
    assert entry.exec_args == ["--arg1", "--arg2"]
    assert entry.details["restart"] == "on-failure"
    assert entry.details["service_type"] == "simple"
    assert entry.details["service_user"] == "nobody"
    assert entry.details["wanted_by"] == "multi-user.target"
    assert entry.details["after"] == "network.target"


def test_parse_unit_timer(tmp_path):
    service_dir = tmp_path / "system"
    service_dir.mkdir()
    timer_file = service_dir / "backup.timer"
    timer_file.write_text(
        "[Unit]\n"
        "Description=Backup Timer\n"
        "\n"
        "[Timer]\n"
        "OnCalendar=daily\n"
        "\n"
        "[Install]\n"
        "WantedBy=timers.target\n"
    )
    scanner = SystemdScanner()
    entry = scanner._parse_unit(str(timer_file), "system")
    assert entry is not None
    assert entry.name == "backup.timer"
    assert entry.enabled is True  # timers are always enabled
    assert "timer" in entry.tags


def test_parse_unit_empty(tmp_path):
    service_dir = tmp_path / "system"
    service_dir.mkdir()
    service_file = service_dir / "empty.service"
    service_file.write_text("")
    scanner = SystemdScanner()
    entry = scanner._parse_unit(str(service_file), "system")
    assert entry is None  # empty file has no sections to parse


def test_parse_unit_broken_symlink(tmp_path):
    service_dir = tmp_path / "system"
    service_dir.mkdir()
    broken_link = service_dir / "broken.service"
    broken_link.symlink_to("/nonexistent/target")
    scanner = SystemdScanner()
    entries = scanner._scan_dir(str(service_dir), "system", set())
    assert len(entries) == 0
