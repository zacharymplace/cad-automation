"""Check the complete calibration coupon, including its lower plate half."""

import json
from pathlib import Path

import cadquery as cq

from zcad.generators.tolerance_coupon import (
    ToleranceCouponParameters,
    build_tolerance_coupon,
)


def test_catalog_coupon_slots_are_open_through_plate():
    path = (
        Path(__file__).parents[1] / "designs/calibration/default-tolerance-coupon.json"
    )
    p = ToleranceCouponParameters(**json.loads(path.read_text())["parameters"])
    shape = build_tolerance_coupon(p).val()
    columns = max(len(p.hole_diameters), len(p.slot_widths))
    left = -(columns - 1) * p.cell_width / 2
    assert shape.isValid()
    assert len(shape.Solids()) == 1
    for i, width in enumerate(p.slot_widths):
        x = left + i * p.cell_width
        y = -p.cell_height / 2
        for z in (-0.49, -0.25, 0, 0.25, 0.49):
            for dx in (-width * 0.4, 0, width * 0.4):
                assert not shape.isInside(cq.Vector(x + dx, y, z * p.plate_thickness))
            assert shape.isInside(
                cq.Vector(x + width / 2 + 0.2, y, z * p.plate_thickness)
            )
