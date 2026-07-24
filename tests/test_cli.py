"""CLI behavior tests."""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(
    design_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Run the ZCAD CLI in a subprocess."""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "src"

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "zcad.cli",
            str(design_path),
        ],
        cwd=Path.cwd(),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_valid_design_exits_successfully(
    tmp_path: Path,
) -> None:
    design_path = Path("designs/example-tray.json")

    result = run_cli(design_path)

    assert result.returncode == 0
    assert "Generated: example-tray" in result.stdout
    assert "Traceback" not in result.stderr


def test_oversized_design_has_clean_error(
    tmp_path: Path,
) -> None:
    design = {
        "name": "oversized-enclosure",
        "type": "enclosure",
        "parameters": {
            "width": 300.0,
            "depth": 70.0,
            "height": 30.0,
            "wall": 3.0,
            "floor": 3.0,
            "lid_thickness": 3.0,
            "lid_clearance": 0.25,
            "lid_lip_height": 4.0,
            "lid_lip_wall": 2.0,
            "corner_radius": 4.0,
            "cable_slot_width": 14.0,
            "cable_slot_height": 8.0,
            "mounting_hole_diameter": 3.2,
            "mounting_hole_spacing_x": 60.0,
            "mounting_hole_spacing_y": 35.0,
            "label": "OVERSIZED",
            "label_size": 6.0,
            "label_height": 0.6,
        },
    }

    design_path = tmp_path / "oversized-enclosure.json"
    design_path.write_text(
        json.dumps(
            design,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_cli(design_path)

    assert result.returncode == 1
    assert "build_volume_x_exceeded" in result.stdout
    assert "zcad: error: Profile-aware validation failed" in result.stderr
    assert "Traceback" not in result.stderr
