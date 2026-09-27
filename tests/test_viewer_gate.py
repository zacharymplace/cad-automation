"""Focused viewer gate integration checks; no full local run required."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from zcad.local_ci import gates, run_gates
from zcad.run_integrity import bind_artifacts


def test_viewer_gate_registered():
    commands = dict(gates(sys.executable))
    assert commands["viewer"] == [sys.executable, "tools/validation-desk/verify.py"]


def test_stale_check_does_not_rewrite(tmp_path):
    source = Path(__file__).resolve().parents[1] / "tools/validation-desk"
    folder = tmp_path / "viewer"
    shutil.copytree(source, folder)
    target = folder / "index.html"
    target.write_bytes(b"stale")
    result = subprocess.run(
        [sys.executable, str(folder / "verify.py")], capture_output=True, check=False
    )
    assert result.returncode != 0
    assert target.read_bytes() == b"stale"


def test_missing_node_is_explicit(tmp_path):
    script = Path(__file__).resolve().parents[1] / "tools/validation-desk/verify.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        env={**os.environ, "PATH": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "requires Node.js" in result.stderr


def test_failed_viewer_continues_and_logs_are_bound(tmp_path):
    receipt = {}
    run_gates(
        tmp_path,
        tmp_path,
        [
            ("viewer", [sys.executable, "-c", "raise SystemExit(1)"]),
            ("later", [sys.executable, "-c", "print('continued')"]),
        ],
        receipt,
        10,
    )
    assert [g["status"] for g in receipt["gates"]] == ["FAIL", "PASS"]
    binding = bind_artifacts(tmp_path, receipt)
    assert set(binding["files"]) == {
        "viewer.stdout.log",
        "viewer.stderr.log",
        "later.stdout.log",
        "later.stderr.log",
    }
