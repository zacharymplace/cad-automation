"""Tests for the travel-case insert tray generator."""

import cadquery as cq
import pytest

from zcad.generators.insert_tray import (
    InsertTrayParameters,
    build_insert_tray,
)


def default_parameters() -> InsertTrayParameters:
    """Return a representative insert-tray specification."""
    return InsertTrayParameters(
        width=170,
        depth=215,
        floor_thickness=3,
        corner_radius=4,
        grip_stand_well_width=66,
        grip_stand_well_depth=102,
        grip_stand_well_wall=3,
        grip_stand_well_wall_height=8,
        ink_cap_tray_well_width=162,
        ink_cap_tray_well_depth=96,
        ink_cap_tray_well_wall=3,
        ink_cap_tray_well_wall_height=6,
        well_gap=8,
    )


def test_insert_tray_is_valid() -> None:
    solid = build_insert_tray(default_parameters()).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_wells_stay_within_the_tray_width() -> None:
    """A well's outer footprint (opening plus its wall) must never
    exceed the tray's own width -- a real bug caught during design:
    the first pass sized the ink cap tray well 1 mm too wide."""
    parameters = default_parameters()
    bounds = build_insert_tray(parameters).val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)


def test_bounds_match_footprint() -> None:
    parameters = default_parameters()
    bounds = build_insert_tray(parameters).val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)
    assert bounds.ylen == pytest.approx(parameters.depth + parameters.label_height)


def test_grip_stand_well_is_open_and_walled() -> None:
    parameters = default_parameters()
    solid = build_insert_tray(parameters).val()

    grip_stand_y, _ink_cap_tray_y = parameters.well_centers_y()
    mid_wall_z = parameters.floor_thickness + parameters.grip_stand_well_wall_height / 2
    wall_x = parameters.grip_stand_well_width / 2 + parameters.grip_stand_well_wall / 2

    assert solid.isInside(cq.Vector(wall_x, grip_stand_y, mid_wall_z))
    assert not solid.isInside(cq.Vector(0, grip_stand_y, mid_wall_z))


def test_ink_cap_tray_well_is_open_and_walled() -> None:
    parameters = default_parameters()
    solid = build_insert_tray(parameters).val()

    _grip_stand_y, ink_cap_tray_y = parameters.well_centers_y()
    mid_wall_z = (
        parameters.floor_thickness + parameters.ink_cap_tray_well_wall_height / 2
    )
    wall_x = (
        parameters.ink_cap_tray_well_width / 2 + parameters.ink_cap_tray_well_wall / 2
    )

    assert solid.isInside(cq.Vector(wall_x, ink_cap_tray_y, mid_wall_z))
    assert not solid.isInside(cq.Vector(0, ink_cap_tray_y, mid_wall_z))


def test_floor_survives_between_the_two_wells() -> None:
    parameters = default_parameters()
    solid = build_insert_tray(parameters).val()

    grip_stand_y, ink_cap_tray_y = parameters.well_centers_y()
    midpoint_y = (grip_stand_y + ink_cap_tray_y) / 2
    mid_floor_z = parameters.floor_thickness / 2

    assert solid.isInside(cq.Vector(0, midpoint_y, mid_floor_z))


def test_wells_are_ordered_front_to_back() -> None:
    parameters = default_parameters()
    grip_stand_y, ink_cap_tray_y = parameters.well_centers_y()

    assert grip_stand_y < ink_cap_tray_y


def test_invalid_insert_tray_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_insert_tray(
            InsertTrayParameters(
                width=10,
                depth=215,
            )
        )


def test_oversized_well_width_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_insert_tray(
            InsertTrayParameters(
                width=170,
                depth=215,
                ink_cap_tray_well_width=166,
            )
        )


def test_oversized_wells_depth_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_insert_tray(
            InsertTrayParameters(
                width=170,
                depth=215,
                grip_stand_well_depth=150,
                ink_cap_tray_well_depth=150,
            )
        )
