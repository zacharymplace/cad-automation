"""CLI tests for the insert-boss calibration coupon."""

import json
from pathlib import Path

from zcad.cli import (
    generate_parts,
    read_design,
)


def test_insert_boss_coupon_design_generates_one_part() -> None:
    design_path = Path("designs/calibration/insert-boss-coupon.json")

    design = read_design(design_path)
    parts = generate_parts(design)

    assert design["type"] == "insert_boss_coupon"
    assert set(parts) == {"main"}
    assert parts["main"].val().isValid()


def test_insert_boss_coupon_design_is_json_object() -> None:
    design_path = Path("designs/calibration/insert-boss-coupon.json")

    data = json.loads(
        design_path.read_text(
            encoding="utf-8",
        )
    )

    assert data["name"] == "insert-boss-coupon"
    assert data["parameters"]["width_mm"] == 120.0
