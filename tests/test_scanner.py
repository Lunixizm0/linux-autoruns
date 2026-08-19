from __future__ import annotations

import os
import tempfile
from pathlib import Path

from linux_autoruns.scanner import BaseScanner, MAX_FILE_SIZE
from linux_autoruns.models import AutostartEntry


class DummyScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Dummy"

    @property
    def description(self) -> str:
        return "Dummy scanner"

    def scan(self) -> list[AutostartEntry]:
        return []


def test_make_entry_defaults():
    scanner = DummyScanner()
    entry = scanner._make_entry(name="test", file_path="/test")
    assert entry.category == "Dummy"
    assert entry.name == "test"
    assert entry.enabled is True
    assert entry.scope == "system"


def test_make_entry_override():
    scanner = DummyScanner()
    entry = scanner._make_entry(name="x", enabled=False, scope="user")
    assert entry.enabled is False
    assert entry.scope == "user"


def test_read_file(tmp_path):
    scanner = DummyScanner()
    f = tmp_path / "test.txt"
    f.write_text("hello world", encoding="utf-8")
    content = scanner._read_file(str(f))
    assert content == "hello world"


def test_read_file_nonexistent():
    scanner = DummyScanner()
    assert scanner._read_file("/nonexistent/file") is None


def test_read_file_too_large(tmp_path):
    scanner = DummyScanner()
    f = tmp_path / "big.txt"
    f.write_bytes(b"x" * (MAX_FILE_SIZE + 1))
    assert scanner._read_file(str(f)) is None


def test_get_mtime_iso(tmp_path):
    scanner = DummyScanner()
    f = tmp_path / "test.txt"
    f.write_text("x")
    mtime = scanner._get_mtime_iso(str(f))
    assert mtime is not None
    assert "T" in mtime


def test_get_mtime_iso_nonexistent():
    scanner = DummyScanner()
    assert scanner._get_mtime_iso("/nonexistent") is None


def test_get_file_info(tmp_path):
    scanner = DummyScanner()
    f = tmp_path / "test.txt"
    f.write_text("hello")
    info = scanner._get_file_info(str(f))
    assert info["size"] == 5
    assert info["permissions"] is not None
    assert info["owner"] is not None


def test_get_file_info_nonexistent():
    scanner = DummyScanner()
    info = scanner._get_file_info("/nonexistent")
    assert info["size"] is None


def test_parse_key_value():
    scanner = DummyScanner()
    content = "key1=value1\n# comment\nkey2=value2\n; another comment\nkey3=value3"
    result = scanner._parse_key_value(content)
    assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}


def test_parse_key_value_empty():
    scanner = DummyScanner()
    assert scanner._parse_key_value("") == {}
    assert scanner._parse_key_value("# just comments") == {}


def test_safe_exists():
    scanner = DummyScanner()
    assert scanner._safe_exists("/") is True
    assert scanner._safe_exists("/nonexistent_path_xyz") is False


def test_glob_files(tmp_path):
    scanner = DummyScanner()
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    (tmp_path / "c.py").write_text("c")
    result = scanner._glob_files(str(tmp_path / "*.txt"))
    assert len(result) == 2


def test_current_user():
    scanner = DummyScanner()
    user = scanner._current_user
    assert user is not None
    assert isinstance(user, str)
