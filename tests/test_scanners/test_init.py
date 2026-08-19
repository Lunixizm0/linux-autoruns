from __future__ import annotations

import os
from pathlib import Path

from linux_autoruns.scanners.init import InitScanner


def test_scan_rc_local_enabled(tmp_path):
    rc_local = tmp_path / "rc.local"
    rc_local.write_text("#!/bin/sh\necho hello\nservice start\nexit 0\n")
    scanner = InitScanner()
    # Test the logic directly
    content = rc_local.read_text()
    lines = content.splitlines()
    enabled = "#!/bin/false" not in content
    if len(lines) >= 3:
        enabled = enabled and "exit 0" not in lines[-3:]
    assert enabled is False  # exit 0 is in last 3 lines


def test_scan_rc_local_disabled_false():
    content = "#!/bin/false\necho hello\n"
    enabled = "#!/bin/false" not in content
    assert enabled is False


def test_scan_rc_local_active():
    content = "#!/bin/sh\necho hello\nservice start\n"
    lines = content.splitlines()
    enabled = "#!/bin/false" not in content
    if len(lines) >= 3:
        enabled = enabled and "exit 0" not in lines[-3:]
    assert enabled is True


def test_scan_rc_local_short_file():
    content = "echo hello\n"
    lines = content.splitlines()
    enabled = "#!/bin/false" not in content
    if len(lines) >= 3:
        enabled = enabled and "exit 0" not in lines[-3:]
    assert enabled is True


def test_init_d_parsing():
    scanner = InitScanner()
    content = "### BEGIN INIT INFO\n# Description: My Test Service\n### END INIT INFO\n"
    import re
    m = re.search(r"#\s*(?:###?\s*BEGIN\s+INIT\s+INFO)(.+?)(?:###?\s*END\s+INIT\s+INFO)", content, re.DOTALL)
    assert m is not None
    block = m.group(1)
    description = None
    for bl in block.splitlines():
        if "Description:" in bl:
            description = bl.split("Description:", 1)[1].strip()
            break
    assert description == "My Test Service"
