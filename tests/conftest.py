from __future__ import annotations

import pytest

from linux_autoruns.models import AutostartEntry


@pytest.fixture
def sample_entry() -> AutostartEntry:
    return AutostartEntry(
        category="Systemd",
        file_path="/etc/systemd/system/docker.service",
        name="docker.service",
        enabled=True,
        command="/usr/bin/dockerd",
        exec_args=["-H", "fd://"],
        user=None,
        scope="system",
        description="Docker Application Container Engine",
        comment=None,
        last_modified="2026-08-15T10:22:00+00:00",
        file_size=2150,
        file_permissions="-rw-r--r--",
        owner="root",
        tags=["boot", "service"],
        details={"unit_type": "service", "wanted_by": "multi-user.target"},
    )


@pytest.fixture
def sample_entries() -> list[AutostartEntry]:
    return [
        AutostartEntry(
            category="Systemd",
            file_path="/etc/systemd/system/docker.service",
            name="docker.service",
            enabled=True,
            command="/usr/bin/dockerd",
            scope="system",
            tags=["boot", "service"],
        ),
        AutostartEntry(
            category="Cron",
            file_path="/etc/crontab",
            name="cron:0 * * * *",
            enabled=True,
            command="/usr/bin/foo",
            user="root",
            scope="system",
            tags=["scheduled", "cron"],
        ),
        AutostartEntry(
            category="Systemd",
            file_path="/etc/systemd/system/old.service",
            name="old.service",
            enabled=False,
            scope="system",
            tags=["boot", "service"],
        ),
    ]
