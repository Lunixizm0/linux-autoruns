from __future__ import annotations

from pathlib import Path

from linux_autoruns.scanners.cron import CronScanner


def test_parse_cron_file_content_basic():
    scanner = CronScanner()
    content = "0 * * * * root /usr/bin/foo\n"
    entries = scanner._parse_cron_file_content("/etc/cron.d/test", content, "system")
    assert len(entries) == 1
    assert entries[0].command == "/usr/bin/foo"
    assert entries[0].details["minute"] == "0"
    assert entries[0].details["hour"] == "*"


def test_parse_cron_file_content_no_user_field():
    scanner = CronScanner()
    content = "*/5 * * * * /usr/bin/bar\n"
    entries = scanner._parse_cron_file_content("root-crontab", content, "system")
    assert len(entries) == 1
    assert entries[0].command == "/usr/bin/bar"


def test_parse_cron_file_content_skips_comments():
    scanner = CronScanner()
    content = "# this is a comment\n0 * * * * root /usr/bin/foo\n"
    entries = scanner._parse_cron_file_content("/etc/cron.d/test", content, "system")
    assert len(entries) == 1


def test_parse_cron_file_content_skips_empty():
    scanner = CronScanner()
    content = "\n\n\n"
    entries = scanner._parse_cron_file_content("/etc/cron.d/test", content, "system")
    assert len(entries) == 0


def test_parse_cron_file_content_short_line():
    scanner = CronScanner()
    content = "0 * * * *\n"
    entries = scanner._parse_cron_file_content("/etc/cron.d/test", content, "system")
    assert len(entries) == 0


def test_parse_cron_file_content_at_schedule():
    scanner = CronScanner()
    content = "@daily root /usr/bin/baz\n"
    entries = scanner._parse_cron_file_content("/etc/cron.d/test", content, "system")
    assert len(entries) == 0  # @ schedules are skipped
