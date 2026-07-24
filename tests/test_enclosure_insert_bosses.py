"""Tests for hardware-driven enclosure insert bosses."""

import pytest

from zcad.generators.enclosure import (
    EnclosureParameters,
    build_enclosure,
)


def test_corner_insert_bosses_are_valid() -> None:
    parts = build_enclosure(
        EnclosureParameters(
            width=100.0,
            depth=70.0,
            height=30.0,
            wall=3.0,
            floor=3.0,
            mounting_hole_spacing_x=60.0,
            mounting_hole_spacing_y=35.0,
            corner_insert_fastener="M3",
        )
    )

    plain_parts = build_enclosure(
        EnclosureParameters(
            width=100.0,
            depth=70.0,
            height=30.0,
            wall=3.0,
            floor=3.0,
            mounting_hole_spacing_x=60.0,
            mounting_hole_spacing_y=35.0,
        )
    )

    body = parts["body"].val()
    plain_body = plain_parts["body"].val()
    bounds = body.BoundingBox()

    assert body.isValid()
    assert bounds.zmin == pytest.approx(-15.0)
    assert bounds.zmax == pytest.approx(15.0)
    assert body.Volume() > plain_body.Volume()


def test_corner_insert_bosses_reject_small_enclosure() -> None:
    with pytest.raises(
        ValueError,
        match="do not fit within enclosure width",
    ):
        build_enclosure(
            EnclosureParameters(
                width=28.0,
                depth=40.0,
                height=20.0,
                wall=3.0,
                floor=3.0,
                mounting_hole_spacing_x=10.0,
                mounting_hole_spacing_y=20.0,
                corner_insert_fastener="M4",
                corner_insert_edge_offset_mm=8.0,
            )
        )
