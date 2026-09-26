"""Tests for the dovetailed pixel garden module."""

from dataclasses import replace

import pytest

from zcad.generators.pixel_garden_module import (
    PixelGardenModuleParameters,
    build_pixel_garden_module,
)


def default_parameters() -> PixelGardenModuleParameters:
    return PixelGardenModuleParameters(
        size=40,
        height=40,
        wall=2,
        floor=2.4,
        drain_hole_diameter=6,
        corner_radius=1.5,
        rail_depth=3,
        rail_base_width=6,
        rail_tip_width=9,
        rail_clearance=0.25,
        rail_end_gap=1,
    )


def test_returns_single_valid_solid() -> None:
    parts = build_pixel_garden_module(default_parameters())

    assert set(parts) == {"main"}
    model = parts["main"]
    assert model.val().isValid()
    assert len(model.solids().vals()) == 1


def test_bounds_include_rails_on_two_faces() -> None:
    parameters = default_parameters()
    bounds = build_pixel_garden_module(parameters)["main"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.size + parameters.rail_depth)
    assert bounds.ylen == pytest.approx(parameters.size + parameters.rail_depth)
    assert bounds.zlen == pytest.approx(parameters.height)


def test_neighbours_mate_at_one_size_pitch() -> None:
    """A second module one pitch along X or Y must clear the first."""
    parameters = default_parameters()
    module = build_pixel_garden_module(parameters)["main"]

    for shift in ((parameters.size, 0.0, 0.0), (0.0, parameters.size, 0.0)):
        neighbour = module.translate(shift)
        overlap = module.intersect(neighbour)

        assert overlap.val().Volume() == pytest.approx(0.0, abs=1e-6)


def test_rail_actually_engages_the_slot() -> None:
    """Pushed closer than the pitch, the rail collides with the slot
    bottom, which proves the rail is inside the slot rather than
    beside it."""
    parameters = default_parameters()
    module = build_pixel_garden_module(parameters)["main"]
    too_close = module.translate((parameters.size - 1.0, 0.0, 0.0))

    assert module.intersect(too_close).val().Volume() > 0


def test_module_is_hollow() -> None:
    parameters = default_parameters()
    volume = build_pixel_garden_module(parameters)["main"].val().Volume()
    solid = parameters.size**2 * parameters.height

    assert 0 < volume < 0.5 * solid


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"rail_tip_width": 5}, "rail_tip_width"),
        ({"rail_tip_width": 14, "rail_depth": 3}, "flank"),
        ({"size": 16}, "soil"),
        ({"floor": 50}, "floor"),
        ({"rail_clearance": -0.1}, "negative"),
    ],
)
def test_invalid_parameters_are_rejected(
    changes: dict[str, float],
    message: str,
) -> None:
    parameters = replace(default_parameters(), **changes)

    with pytest.raises(ValueError, match=message):
        build_pixel_garden_module(parameters)
