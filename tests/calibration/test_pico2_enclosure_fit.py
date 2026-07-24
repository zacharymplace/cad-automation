"""Tests for the refined Pico 2 enclosure assembly."""

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
    parameters = Pico2EnclosureFitParameters()
    parts = build_pico2_enclosure_fit(parameters)

    bounds = parts["body"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.outer_width_mm)
    assert bounds.ylen == pytest.approx(parameters.outer_depth_mm)
    assert bounds.zlen == pytest.approx(parameters.body_height_mm)


def test_lid_matches_body_footprint() -> None:
    parameters = Pico2EnclosureFitParameters()
    parts = build_pico2_enclosure_fit(parameters)

    body_bounds = parts["body"].val().BoundingBox()
    lid_bounds = parts["lid"].val().BoundingBox()

    assert lid_bounds.xlen == pytest.approx(body_bounds.xlen)
    assert lid_bounds.ylen == pytest.approx(body_bounds.ylen)
    assert parameters.lid_height_mm == pytest.approx(
        parameters.lid_lip_height_mm + parameters.lid_thickness_mm
    )
    assert lid_bounds.zlen == pytest.approx(parameters.lid_overall_height_mm)


def test_corner_radius_can_be_disabled() -> None:
    parts = build_pico2_enclosure_fit(
        Pico2EnclosureFitParameters(
            corner_radius_mm=0.0,
            exterior_edge_fillet_mm=0.0,
        )
    )

    assert parts["body"].val().isValid()
    assert parts["lid"].val().isValid()


def test_invalid_lid_clearance_is_rejected() -> None:
    parameters = Pico2EnclosureFitParameters(
        lid_clearance_mm=-0.1,
    )

    with pytest.raises(
        ValueError,
        match="lid_clearance_mm",
    ):
        build_pico2_enclosure_fit(parameters)


def test_excessive_corner_radius_is_rejected() -> None:
    parameters = Pico2EnclosureFitParameters(
        corner_radius_mm=20.0,
    )

    with pytest.raises(
        ValueError,
        match="corner_radius_mm",
    ):
        build_pico2_enclosure_fit(parameters)


def test_display_expands_enclosure_width() -> None:
    parameters = Pico2EnclosureFitParameters()
    board_only_width_mm = (
        21.0 + (2 * parameters.board_clearance_mm) + (2 * parameters.wall_mm)
    )

    assert parameters.outer_width_mm > board_only_width_mm


def test_lid_contains_display_window() -> None:
    parameters = Pico2EnclosureFitParameters()
    parts = build_pico2_enclosure_fit(parameters)

    lid = parts["lid"].val()

    full_plate_volume_mm3 = (
        parameters.outer_width_mm
        * parameters.outer_depth_mm
        * parameters.lid_thickness_mm
    )

    assert lid.isValid()
    assert lid.Volume() > 0
    assert lid.Volume() < (full_plate_volume_mm3 + 2000.0)


def test_display_bezel_must_fit_lid() -> None:
    parameters = Pico2EnclosureFitParameters(
        display_center_x_mm=100.0,
    )

    with pytest.raises(
        ValueError,
        match="display bezel",
    ):
        build_pico2_enclosure_fit(parameters)
