"""Tests for the pixel wall hook."""

from dataclasses import replace

import cadquery as cq
import pytest

from zcad.generators.pixel_hook import (
    PixelHookParameters,
    build_pixel_hook,
)


def default_parameters() -> PixelHookParameters:
    return PixelHookParameters(
        width=40,
        plate_thickness=4,
        plate_height=70,
        arm_length=30,
        arm_thickness=5,
        lip_height=12,
        lip_thickness=4,
        corner_radius=1.5,
        screw_hole_diameter=4.2,
        countersink_diameter=8.5,
        hole_inset=6,
        pixel_size=5,
        relief_depth=1.0,
        pixel_inset=0.2,
    )


def test_returns_single_valid_solid() -> None:
    parts = build_pixel_hook(default_parameters())

    assert set(parts) == {"main"}
    model = parts["main"]
    assert model.val().isValid()
    assert len(model.solids().vals()) == 1


def test_bounds_span_reach_width_and_plate_height() -> None:
    parameters = default_parameters()
    bounds = build_pixel_hook(parameters)["main"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.reach)
    assert bounds.ylen == pytest.approx(parameters.width)
    assert bounds.zlen == pytest.approx(parameters.plate_height)
    assert bounds.xmin == pytest.approx(0.0)


def test_screw_holes_pass_through_the_plate() -> None:
    parameters = default_parameters()
    model = build_pixel_hook(parameters)["main"].val()

    for z in parameters.hole_centers_z:
        assert not model.isInside(cq.Vector(parameters.plate_thickness / 2, 0.0, z))

    # Between the holes the plate is solid behind the relief.
    mid = parameters.relief_center_z
    assert model.isInside(cq.Vector(0.5, 0.0, mid))


def test_relief_is_recessed_from_the_front_face() -> None:
    parameters = default_parameters()
    model = build_pixel_hook(parameters)["main"].val()
    grid = parameters.grid
    pt = parameters.plate_thickness
    probe_x = pt - parameters.relief_depth / 2

    u, v = grid.pixel_center((0, 4))  # note head pixel, filled
    blank_u, blank_v = grid.pixel_center((0, 0))  # empty

    assert not model.isInside(cq.Vector(probe_x, -u, parameters.relief_center_z + v))
    assert model.isInside(
        cq.Vector(probe_x, -blank_u, parameters.relief_center_z + blank_v)
    )


def test_lip_rises_above_the_arm() -> None:
    parameters = default_parameters()
    model = build_pixel_hook(parameters)["main"].val()
    lip_x = parameters.reach - parameters.lip_thickness / 2
    arm_x = parameters.plate_thickness + parameters.arm_length / 2

    assert model.isInside(cq.Vector(lip_x, 0.0, parameters.lip_height - 1.0))
    assert not model.isInside(cq.Vector(arm_x, 0.0, parameters.lip_height - 1.0))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"corner_radius": 2.5}, "corner_radius"),
        ({"countersink_diameter": 4.0}, "countersink_diameter"),
        ({"relief_depth": 3.0}, "relief_depth"),
        ({"lip_height": 4.0}, "lip_height"),
        ({"plate_height": 30}, "plate_height"),
        ({"pixel_size": 8}, "pattern"),
    ],
)
def test_invalid_parameters_are_rejected(
    changes: dict[str, object],
    message: str,
) -> None:
    parameters = replace(default_parameters(), **changes)

    with pytest.raises(ValueError, match=message):
        build_pixel_hook(parameters)
