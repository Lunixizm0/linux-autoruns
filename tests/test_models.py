from __future__ import annotations

from linux_autoruns.models import AutostartEntry


def test_entry_creation():
    entry = AutostartEntry(
        category="Test",
        file_path="/test",
        name="test",
        enabled=True,
    )
    assert entry.category == "Test"
    assert entry.enabled is True
    assert entry.command is None
    assert entry.tags == []
    assert entry.details == {}


def test_entry_to_dict(sample_entry):
    d = sample_entry.to_dict()
    assert d["category"] == "Systemd"
    assert d["name"] == "docker.service"
    assert d["enabled"] is True
    assert d["command"] == "/usr/bin/dockerd"
    assert d["exec_args"] == ["-H", "fd://"]
    assert d["tags"] == ["boot", "service"]
    assert d["details"]["unit_type"] == "service"


def test_entry_defaults():
    entry = AutostartEntry(
        category="X",
        file_path="/x",
        name="x",
        enabled=False,
    )
    assert entry.user is None
    assert entry.scope == "system"
    assert entry.description is None
    assert entry.last_modified is None
    assert entry.file_size is None


def test_entry_with_details():
    entry = AutostartEntry(
        category="Cron",
        file_path="/etc/crontab",
        name="test",
        enabled=True,
        details={"schedule": "0 * * * *", "user": "root"},
    )
    assert entry.details["schedule"] == "0 * * * *"
    assert entry.details["user"] == "root"
