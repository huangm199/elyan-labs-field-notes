#!/usr/bin/env python3
"""Verify ClawRTC dry-run behavior in an isolated HOME on Linux."""
from __future__ import annotations

import os
from pathlib import Path
import platform
import subprocess
import tempfile


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("This preflight regression check is intentionally Linux-only.")

    with tempfile.TemporaryDirectory(prefix="clawrtc-home-") as temp_home:
        env = os.environ.copy()
        env["HOME"] = temp_home
        proc = subprocess.run(
            ["clawrtc", "install", "--dry-run", "--wallet", "field-notes-demo"],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        output = proc.stdout + proc.stderr
        install_dir = Path(temp_home) / ".clawrtc"

        assert proc.returncode == 0, output
        assert "DRY RUN" in output, output
        assert not install_dir.exists(), f"dry-run unexpectedly created {install_dir}"

        platform_line = next(
            (line.strip() for line in output.splitlines() if "Platform:" in line),
            "Platform line not found",
        )
        print("PASS: clawrtc dry-run returned 0")
        print("PASS: output explicitly reported DRY RUN")
        print("PASS: temporary ~/.clawrtc was not created")
        print(f"platform_line: {platform_line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
