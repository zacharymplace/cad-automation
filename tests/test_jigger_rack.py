"""Tests for the home-bar jigger rack generator."""

import cadquery as cq
import pytest

from zcad.generators.jigger_rack import JiggerRackParameters, build_jigger_rack


def default_parameters() -> JiggerRackParameters:
    """Return a representative jigger-rack specification."""
    return JiggerRackParameters(
        width=220,
        depth=80,
        base_thickness=3,
        leg_height=50,
        leg_diameter=10,
        leg_inset=14,
        rack_thickness=4,
        jigger_count=4,
        jigger_hole_diameter=35,
        jigger_spacing=45,
        jigger_hole_chamfer=1.5,
    )


def test_jigger_rack_is_valid() -> None:
    solid = build_jigger_rack(default_parameters()).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_bounds_match_footprint_and_full_height() -> None:
    parameters = default_parameters()
    bounds = build_jigger_rack(parameters).val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)
    assert bounds.ylen == pytest.approx(parameters.depth)
    assert bounds.zlen == pytest.approx(
        parameters.base_thickness + parameters.leg_height + parameters.rack_thickness
    )


def test_legs_are_solid_and_inset_from_the_corners() -> None:
    parameters = default_parameters()
    solid = build_jigger_rack(parameters).val()

    leg_mid_z = parameters.base_thickness + parameters.leg_height / 2

    for x, y in parameters.leg_positions():
        assert solid.isInside(cq.Vector(x, y, leg_mid_z))
        assert abs(x) < parameters.width / 2
        assert abs(y) < parameters.depth / 2


def test_base_plate_is_solid_beneath_the_legs() -> None:
    parameters = default_parameters()
    solid = build_jigger_rack(parameters).val()

    base_mid_z = parameters.base_thickness / 2
    assert solid.isInside(cq.Vector(0, 0, base_mid_z))


def test_jigger_holes_are_open_and_ordered() -> None:
    parameters = default_parameters()
    solid = build_jigger_rack(parameters).val()

    centers = parameters.jigger_hole_centers_x()
    assert len(centers) == parameters.jigger_count
    assert centers == sorted(centers)

    plate_mid_z = (
        parameters.base_thickness
        + parameters.leg_height
        + parameters.rack_thickness / 2
    )

    for center_x in centers:
        assert not solid.isInside(cq.Vector(center_x, 0, plate_mid_z))


def test_rack_plate_is_solid_between_holes() -> None:
    parameters = default_parameters()
    solid = build_jigger_rack(parameters).val()

    centers = parameters.jigger_hole_centers_x()
    midpoint_x = (centers[0] + centers[1]) / 2
    plate_mid_z = (
        parameters.base_thickness
        + parameters.leg_height
        + parameters.rack_thickness / 2
    )

    assert solid.isInside(cq.Vector(midpoint_x, 0, plate_mid_z))


def test_hole_chamfer_widens_the_top_mouth_only() -> None:
    """The countersink should widen the hole near the top surface but
    leave a straight bore near the bottom -- otherwise the frustum
    isn't oriented the way a countersink needs to be."""
    parameters = default_parameters()
    solid = build_jigger_rack(parameters).val()

    plate_bottom_z = parameters.base_thickness + parameters.leg_height
    near_top_z = plate_bottom_z + parameters.rack_thickness - 0.05
    near_bottom_z = plate_bottom_z + 0.05

    hole_x = parameters.jigger_hole_centers_x()[0]
    widened_radius = (
        parameters.jigger_hole_diameter / 2 + parameters.jigger_hole_chamfer / 2
    )

    assert not solid.isInside(cq.Vector(hole_x + widened_radius, 0, near_top_z))
    assert solid.isInside(cq.Vector(hole_x + widened_radius, 0, near_bottom_z))


def test_hole_chamfer_can_be_disabled() -> None:
    parameters = JiggerRackParameters(
        width=220,
        depth=80,
        jigger_hole_chamfer=0,
    )
    solid = build_jigger_rack(parameters).val()

    plate_bottom_z = parameters.base_thickness + parameters.leg_height
    near_top_z = plate_bottom_z + parameters.rack_thickness - 0.05

    hole_x = parameters.jigger_hole_centers_x()[0]
    widened_radius = parameters.jigger_hole_diameter / 2 + 0.5

    assert solid.isInside(cq.Vector(hole_x + widened_radius, 0, near_top_z))


def test_invalid_jigger_rack_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_jigger_rack(
            JiggerRackParameters(
                width=10,
                depth=80,
            )
        )


def test_too_many_jiggers_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_jigger_rack(
            JiggerRackParameters(
                width=220,
                depth=80,
                jigger_count=10,
            )
        )


def test_oversized_leg_inset_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_jigger_rack(
            JiggerRackParameters(
                width=220,
                depth=80,
                leg_inset=100,
            )
        )


def test_undersized_leg_inset_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_jigger_rack(
            JiggerRackParameters(
                width=220,
                depth=80,
                leg_diameter=10,
                leg_inset=2,
            )
        )


def test_overlapping_countersinks_are_rejected() -> None:
    with pytest.raises(ValueError):
        build_jigger_rack(
            JiggerRackParameters(
                width=220,
                depth=80,
                rack_thickness=8,
                jigger_spacing=38,
                jigger_hole_chamfer=3,
            )
        )
