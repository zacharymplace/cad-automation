"""Tests for the Pico 2 enclosure assembly."""

import cadquery as cq
import pytest

from zcad.generators.calibration.pico2_enclosure_fit import (
    Pico2EnclosureFitParameters,
    build_pico2_enclosure_fit,
)


def test_enclosure_returns_body_and_lid() -> None:
    parts = build_pico2_enclosure_fit(Pico2EnclosureFitParameters())

    assert set(parts) == {
        "body",
        "lid",
    }

    for part in parts.values():
        assert isinstance(part, cq.Workplane)
        assert part.val().isValid()
        assert part.val().Volume() > 0


def test_body_dimensions() -> None:
    parts = build_pico2_enclosure_fit(Pico2EnclosureFitParameters())

    bounds = parts["body"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(29.0)
    assert bounds.ylen == pytest.approx(59.0)
    assert bounds.zlen == pytest.approx(10.0)


def test_lid_matches_body_footprint() -> None:
    parts = build_pico2_enclosure_fit(Pico2EnclosureFitParameters())

    body_bounds = parts["body"].val().BoundingBox()
    lid_bounds = parts["lid"].val().BoundingBox()

    assert lid_bounds.xlen == pytest.approx(body_bounds.xlen)
    assert lid_bounds.ylen == pytest.approx(body_bounds.ylen)
    assert lid_bounds.zlen == pytest.approx(4.5)


def test_invalid_lid_clearance_is_rejected() -> None:
    parameters = Pico2EnclosureFitParameters(
        lid_clearance_mm=-0.1,
    )

    with pytest.raises(
        ValueError,
        match="lid_clearance_mm",
    ):
        build_pico2_enclosure_fit(parameters)
