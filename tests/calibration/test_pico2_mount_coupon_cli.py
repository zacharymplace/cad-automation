"""CLI tests for the Raspberry Pi Pico 2 mount coupon."""

import json
from pathlib import Path

from zcad.cli import (
    generate_parts,
    read_design,
)


def test_cli_generates_pico2_mount_coupon() -> None:
    design = read_design(Path("designs/calibration/pico2-mount-coupon.json"))

    parts = generate_parts(design)

    assert design["type"] == "pico2_mount_coupon"
    assert set(parts) == {"main"}
    assert parts["main"].val().isValid()


def test_minimal_design_generates_coupon(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "pico2.json"

    design_path.write_text(
        json.dumps(
            {
                "name": "pico2-test",
                "type": "pico2_mount_coupon",
                "parameters": {},
            }
        ),
        encoding="utf-8",
    )

    parts = generate_parts(read_design(design_path))

    assert parts["main"].val().isValid()
