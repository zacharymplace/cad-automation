"""CLI tests for the display-window calibration coupon."""

import json
from pathlib import Path

from zcad.cli import (
    generate_parts,
    read_design,
)


def test_cli_generates_display_window_coupon() -> None:
    design = read_design(Path("designs/calibration/display-window-coupon.json"))

    parts = generate_parts(design)

    assert design["type"] == ("display_window_coupon")
    assert set(parts) == {
        "main",
    }
    assert parts["main"].val().isValid()


def test_minimal_design_generates_coupon(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "display-window-coupon.json"

    design_path.write_text(
        json.dumps(
            {
                "name": "display-window-test",
                "type": "display_window_coupon",
                "parameters": {},
            }
        ),
        encoding="utf-8",
    )

    parts = generate_parts(read_design(design_path))

    assert parts["main"].val().isValid()
