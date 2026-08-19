from __future__ import annotations

import os

import pytest

from linux_autoruns.gui.models import (EntryFilterProxy, EntryTableModel,
                                       _format_size, _parse_search_query)
from linux_autoruns.models import AutostartEntry


# _format_size
class TestFormatSize:
    def test_none(self):
        assert _format_size(None) == ""

    def test_zero_bytes(self):
        assert _format_size(0) == "0 B"

    def test_bytes(self):
        assert _format_size(512) == "512 B"

    def test_one_byte_below_kb(self):
        assert _format_size(1023) == "1023 B"

    def test_one_kb(self):
        assert _format_size(1024) == "1.0 KB"

    def test_kilobytes(self):
        assert _format_size(1536) == "1.5 KB"
        assert _format_size(5120) == "5.0 KB"

    def test_one_mb(self):
        assert _format_size(1048576) == "1.0 MB"

    def test_megabytes(self):
        assert _format_size(2621440) == "2.5 MB"

# EntryTableModel
def _make_entry(**overrides) -> AutostartEntry:
    defaults = dict(
        category="Systemd",
        file_path="/etc/systemd/system/test.service",
        name="test.service",
        enabled=True,
    )
    defaults.update(overrides)
    return AutostartEntry(**defaults)


class TestTableModelHeaders:
    def test_column_count(self):
        model = EntryTableModel()
        assert model.columnCount() == 12

    def test_headers_are_strings(self):
        for h in EntryTableModel.HEADERS:
            assert isinstance(h, str)

    def test_first_header_is_plus(self):
        assert EntryTableModel.HEADERS[0] == "+"

    def test_known_headers(self):
        assert "Name" in EntryTableModel.HEADERS
        assert "Category" in EntryTableModel.HEADERS
        assert "Command" in EntryTableModel.HEADERS
        assert "Path" in EntryTableModel.HEADERS
        assert "Scope" in EntryTableModel.HEADERS
        assert "Perms" in EntryTableModel.HEADERS
        assert "Size" in EntryTableModel.HEADERS
        assert "Modified" in EntryTableModel.HEADERS
        assert "Owner" in EntryTableModel.HEADERS

    def test_header_data(self):
        model = EntryTableModel()
        from PySide6.QtCore import Qt
        assert model.headerData(0, Qt.Horizontal) == "+"
        assert model.headerData(1, Qt.Horizontal) == "Name"
        assert model.headerData(11, Qt.Horizontal) == "Owner"


class TestTableModelData:
    def test_empty_model(self):
        model = EntryTableModel()
        assert model.rowCount() == 0
        assert model.columnCount() == 12

    def test_add_entry(self):
        model = EntryTableModel()
        entry = _make_entry()
        model.add_entry(entry)
        assert model.rowCount() == 1
        assert model.entry_at(0) is entry

    def test_set_entries(self):
        model = EntryTableModel()
        entries = [_make_entry(name=f"svc{i}.service") for i in range(5)]
        model.set_entries(entries)
        assert model.rowCount() == 5
        assert model.entry_at(3).name == "svc3.service"

    def test_get_all_entries_returns_copy(self):
        model = EntryTableModel()
        entry = _make_entry()
        model.set_entries([entry])
        result = model.get_all_entries()
        assert len(result) == 1
        result.clear()
        assert model.rowCount() == 1

    def test_entry_at_out_of_range(self):
        model = EntryTableModel()
        assert model.entry_at(0) is None
        assert model.entry_at(-1) is None
        assert model.entry_at(999) is None

    def test_col0_enabled_shows_plus(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(enabled=True)])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 0), Qt.DisplayRole)
        assert val == "+"

    def test_col0_disabled_shows_minus(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(enabled=False)])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 0), Qt.DisplayRole)
        assert val == "-"

    def test_col1_returns_name(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(name="my.service")])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 1), Qt.DisplayRole)
        assert val == "my.service"

    def test_col9_returns_formatted_size(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(file_size=2048)])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 9), Qt.DisplayRole)
        assert val == "2.0 KB"

    def test_col9_none_size_returns_empty(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(file_size=None)])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 9), Qt.DisplayRole)
        assert val == ""

    def test_col5_returns_command(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(command="/usr/bin/foo")])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 5), Qt.DisplayRole)
        assert val == "/usr/bin/foo"

    def test_col6_returns_path(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(file_path="/some/path")])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 6), Qt.DisplayRole)
        assert val == "/some/path"

    def test_col5_truncates_long_command(self):
        model = EntryTableModel()
        long_cmd = "/usr/bin/very-long-command --arg1 foo --arg2 bar --arg3 baz"
        model.set_entries([_make_entry(command=long_cmd)])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 5), Qt.DisplayRole)
        assert val.endswith("...")
        assert len(val) == 50

    def test_col6_truncates_long_path(self):
        model = EntryTableModel()
        long_path = "/some/very/long/path/to/a/file/that/definitely/exceeds/limit"
        model.set_entries([_make_entry(file_path=long_path)])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 6), Qt.DisplayRole)
        assert val.endswith("...")
        assert len(val) == 50

    def test_col5_short_command_not_truncated(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(command="/usr/bin/short")])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 5), Qt.DisplayRole)
        assert val == "/usr/bin/short"
        assert "..." not in val

    def test_col11_returns_owner(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(owner="nobody")])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 11), Qt.DisplayRole)
        assert val == "nobody"

    def test_user_role_returns_entry_object(self):
        model = EntryTableModel()
        entry = _make_entry()
        model.set_entries([entry])
        from PySide6.QtCore import Qt
        val = model.data(model.index(0, 0), Qt.UserRole)
        assert val is entry


class TestTableModelColors:
    def test_foreground_green_when_enabled(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(enabled=True)])
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor
        color = model.data(model.index(0, 0), Qt.ForegroundRole)
        assert isinstance(color, QColor)
        assert color.name() == "#a6e3a1"

    def test_foreground_red_when_disabled(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(enabled=False)])
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor
        color = model.data(model.index(0, 0), Qt.ForegroundRole)
        assert isinstance(color, QColor)
        assert color.name() == "#f38ba8"

    def test_foreground_blue_for_name(self):
        model = EntryTableModel()
        model.set_entries([_make_entry()])
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor
        color = model.data(model.index(0, 1), Qt.ForegroundRole)
        assert isinstance(color, QColor)
        assert color.name() == "#89b4fa"

    def test_background_yellow_for_missing_file(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(file_path="/nonexistent/path/file")])
        from PySide6.QtCore import Qt
        bg = model.data(model.index(0, 1), Qt.BackgroundRole)
        assert bg is not None
        assert bg.red() == 249
        assert bg.green() == 226
        assert bg.blue() == 175

    def test_background_none_for_existing_file(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(file_path=__file__)])
        from PySide6.QtCore import Qt
        bg = model.data(model.index(0, 1), Qt.BackgroundRole)
        assert bg is None

    def test_background_none_for_col0(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(file_path="/nonexistent")])
        from PySide6.QtCore import Qt
        bg = model.data(model.index(0, 0), Qt.BackgroundRole)
        assert bg is None

    def test_tooltip_on_command_col(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(command="/usr/bin/test", exec_args=["--flag"])])
        from PySide6.QtCore import Qt
        tip = model.data(model.index(0, 5), Qt.ToolTipRole)
        assert "Command: /usr/bin/test" in tip
        assert "Args: --flag" in tip

    def test_tooltip_on_path_col(self):
        model = EntryTableModel()
        model.set_entries([_make_entry(file_path="/some/file")])
        from PySide6.QtCore import Qt
        tip = model.data(model.index(0, 6), Qt.ToolTipRole)
        assert "Path: /some/file" in tip

    def test_tooltip_none_for_other_cols(self):
        model = EntryTableModel()
        model.set_entries([_make_entry()])
        from PySide6.QtCore import Qt
        assert model.data(model.index(0, 1), Qt.ToolTipRole) is None

    def test_font_bold_for_col0(self):
        model = EntryTableModel()
        model.set_entries([_make_entry()])
        from PySide6.QtCore import Qt
        font = model.data(model.index(0, 0), Qt.FontRole)
        assert font is not None
        assert font.bold()

    def test_alignment_center_for_col0(self):
        model = EntryTableModel()
        model.set_entries([_make_entry()])
        from PySide6.QtCore import Qt
        align = model.data(model.index(0, 0), Qt.TextAlignmentRole)
        assert align == int(Qt.AlignCenter)

    def test_alignment_right_for_size_col(self):
        model = EntryTableModel()
        model.set_entries([_make_entry()])
        from PySide6.QtCore import Qt
        align = model.data(model.index(0, 9), Qt.TextAlignmentRole)
        assert align == int(Qt.AlignRight | Qt.AlignVCenter)


class TestTableModelInvalidIndex:
    def test_invalid_index_returns_none(self):
        model = EntryTableModel()
        from PySide6.QtCore import QModelIndex
        assert model.data(QModelIndex()) is None

# EntryFilterProxy
def _proxy_with_entries(entries) -> EntryFilterProxy:
    model = EntryTableModel()
    model.set_entries(entries)
    proxy = EntryFilterProxy()
    proxy.setSourceModel(model)
    return proxy, model


class TestFilterProxy:
    def test_no_filter_shows_all(self):
        entries = [
            _make_entry(name="a"),
            _make_entry(name="b"),
            _make_entry(name="c"),
        ]
        proxy, _ = _proxy_with_entries(entries)
        assert proxy.rowCount() == 3

    def test_category_filter(self):
        entries = [
            _make_entry(name="a", category="Systemd"),
            _make_entry(name="b", category="Cron"),
            _make_entry(name="c", category="Systemd"),
        ]
        proxy, _ = _proxy_with_entries(entries)
        proxy.set_category_filter("Cron")
        assert proxy.rowCount() == 1

    def test_enabled_only_filter(self):
        entries = [
            _make_entry(name="a", enabled=True),
            _make_entry(name="b", enabled=False),
        ]
        proxy, _ = _proxy_with_entries(entries)
        proxy.set_enabled_only(True)
        assert proxy.rowCount() == 1

    def test_scope_filter(self):
        entries = [
            _make_entry(name="a", scope="system"),
            _make_entry(name="b", scope="user"),
        ]
        proxy, _ = _proxy_with_entries(entries)
        proxy.set_scope_filter("user")
        assert proxy.rowCount() == 1

    def test_tag_filter(self):
        entries = [
            _make_entry(name="a", tags=["boot"]),
            _make_entry(name="b", tags=["login"]),
        ]
        proxy, _ = _proxy_with_entries(entries)
        proxy.set_tag_filter("boot")
        assert proxy.rowCount() == 1

    def test_search_text(self):
        entries = [
            _make_entry(name="docker.service"),
            _make_entry(name="nginx.service"),
        ]
        proxy, _ = _proxy_with_entries(entries)
        proxy.set_search_text("docker")
        assert proxy.rowCount() == 1

    def test_search_key_value(self):
        entries = [
            _make_entry(name="foo", command="/usr/bin/foo"),
            _make_entry(name="bar", command="/usr/bin/bar"),
        ]
        proxy, _ = _proxy_with_entries(entries)
        proxy.set_search_text("command:/usr/bin/foo")
        assert proxy.rowCount() == 1

    def test_search_enabled_true(self):
        entries = [
            _make_entry(name="a", enabled=True),
            _make_entry(name="b", enabled=False),
        ]
        proxy, _ = _proxy_with_entries(entries)
        proxy.set_search_text("enabled:true")
        assert proxy.rowCount() == 1

    def test_search_disabled_true(self):
        entries = [
            _make_entry(name="a", enabled=True),
            _make_entry(name="b", enabled=False),
        ]
        proxy, _ = _proxy_with_entries(entries)
        proxy.set_search_text("disabled:true")
        assert proxy.rowCount() == 1

    def test_combined_filters(self):
        entries = [
            _make_entry(name="a", category="Systemd", enabled=True),
            _make_entry(name="b", category="Cron", enabled=True),
            _make_entry(name="c", category="Systemd", enabled=False),
        ]
        proxy, _ = _proxy_with_entries(entries)
        proxy.set_category_filter("Systemd")
        proxy.set_enabled_only(True)
        assert proxy.rowCount() == 1

# _parse_search_query
class TestParseSearchQuery:
    def test_simple_word(self):
        result = _parse_search_query("docker")
        assert len(result) == 1
        assert result[0] == (None, "docker")

    def test_key_value(self):
        result = _parse_search_query("name:nginx")
        assert result[0] == ("name", "nginx")

    def test_key_quoted_value(self):
        result = _parse_search_query('command:"docker daemon"')
        assert result[0] == ("command", "docker daemon")

    def test_multiple_tokens(self):
        result = _parse_search_query("docker enabled:true")
        assert len(result) == 2

    def test_empty_string(self):
        result = _parse_search_query("")
        assert result == []
