"""Tests for the curl installer."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_installer_uses_existing_uv(tmp_path: Path) -> None:
    uv = tmp_path / "uv"
    log = tmp_path / "args"
    uv.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" > "{log}"\n')
    uv.chmod(0o755)

    result = subprocess.run(
        ["sh", str(ROOT / "install.sh")],
        env={**os.environ, "PATH": f"{tmp_path}:/bin:/usr/bin"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert log.read_text() == "tool install --upgrade khmerthings\n"
