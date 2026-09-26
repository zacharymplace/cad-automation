"""Garden-module parameter boundaries and geometric postconditions."""

from dataclasses import fields, replace
from math import pi

import cadquery as cq
import pytest

from zcad.generators.pixel_garden_module import (
    PixelGardenModuleParameters,
    build_module,
    build_pixel_garden_module,
)


@pytest.mark.parametrize("name", [f.name for f in fields(PixelGardenModuleParameters)])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_parameters_are_rejected_before_cad(name, value):
    with pytest.raises(ValueError, match=f"{name} must be a finite"):
        replace(PixelGardenModuleParameters(), **{name: value}).validate()


@pytest.mark.parametrize("value", [True, False, "40", None])
def test_non_numeric_dimensions_are_rejected(value):
    with pytest.raises(ValueError, match="size must be a finite"):
        replace(PixelGardenModuleParameters(), size=value).validate()


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"corner_radius": 2.01}, "corner_radius"),
        ({"corner_radius": 8}, "corner_radius"),
        ({"rail_clearance": 1.5}, "undercut"),
        ({"rail_clearance": 2}, "undercut"),
        ({"rail_end_gap": 40}, "rail_end_gap"),
        ({"drain_hole_diameter": 32.75}, "drain_hole_diameter"),
        ({"size": 17.24}, "soil"),
    ],
)
def test_analytic_boundaries_reject_invalid_combinations(changes, message):
    with pytest.raises(ValueError, match=message):
        replace(PixelGardenModuleParameters(), **changes).validate()


def test_direct_builder_cannot_bypass_parameter_validation():
    with pytest.raises(ValueError, match="height"):
        build_module(replace(PixelGardenModuleParameters(), height=-1))


def test_intersecting_slots_cannot_return_disconnected_corner():
    parameters = replace(
        PixelGardenModuleParameters(), size=30, rail_depth=10, rail_tip_width=20
    )
    with pytest.raises(ValueError, match="one valid connected solid"):
        build_pixel_garden_module(parameters)


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"size": 17.25, "corner_radius": 2},
        {"rail_clearance": 0, "rail_end_gap": 0, "corner_radius": 0},
        {"rail_clearance": 1.49},
        {"wall": 3, "floor": 3, "drain_hole_diameter": 0, "corner_radius": 3},
    ],
)
def test_supported_boundaries_remain_single_solid_and_mate_in_both_axes(changes):
    parameters = replace(PixelGardenModuleParameters(), **changes)
    module = build_module(parameters)
    assert len(module.solids().vals()) == 1
    assert module.val().isValid()
    for shift in ((parameters.size, 0, 0), (0, parameters.size, 0)):
        overlap = module.intersect(module.translate(shift))
        assert overlap.val().Volume() == pytest.approx(0, abs=1e-6)


@pytest.mark.parametrize("axis", [0, 1])
def test_dovetail_retains_against_sideways_separation_without_body_collision(axis):
    parameters = PixelGardenModuleParameters()
    module = build_module(parameters)
    shift = [0, 0, 0]
    # Positive gap separates the cup bodies. Any remaining intersection is
    # therefore retaining rail/slot material, unlike pushing the cups together.
    shift[axis] = parameters.size + parameters.rail_depth / 2
    assert module.intersect(module.translate(tuple(shift))).val().Volume() > 1e-6


@pytest.mark.parametrize("diameter", [0, 6, 20])
def test_drain_is_centered_in_offset_cavity_and_only_removes_floor(diameter):
    parameters = replace(PixelGardenModuleParameters(), drain_hole_diameter=diameter)
    closed = build_module(replace(parameters, drain_hole_diameter=0))
    drained = build_module(parameters)
    removed = closed.val().Volume() - drained.val().Volume()
    assert removed == pytest.approx(
        pi * (diameter / 2) ** 2 * parameters.floor, abs=1e-5
    )
    if diameter:
        center = (parameters.slot_wall - parameters.wall) / 2
        probe = (
            cq.Workplane("XY")
            .center(center, center)
            .circle(diameter / 2 - 0.01)
            .extrude(parameters.floor)
        )
        assert drained.intersect(probe).val().Volume() == pytest.approx(0, abs=1e-6)
        assert closed.intersect(probe).val().Volume() > 0
