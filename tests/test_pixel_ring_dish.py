"""Tests for the pixel ring dish."""

from dataclasses import replace

import pytest

from zcad.generators.pixel_ring_dish import (
    PixelRingDishParameters,
    build_pixel_ring_dish,
)


def default_parameters() -> PixelRingDishParameters:
    return PixelRingDishParameters(
        pixel_size=10,
        wall=2.4,
        floor=3,
        rim_height=12,
        groove_depth=0.5,
        groove_width=0.8,
        cone_pixel=(3, 4),
        cone_base_diameter=18,
        cone_top_diameter=10,
        cone_height=32,
    )


def test_returns_single_valid_solid() -> None:
    parts = build_pixel_ring_dish(default_parameters())

    assert set(parts) == {"main"}
    model = parts["main"]
    assert model.val().isValid()
    assert len(model.solids().vals()) == 1


def test_cone_rises_from_floor_to_total_height() -> None:
    parameters = default_parameters()
    bounds = build_pixel_ring_dish(parameters)["main"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.grid.width)
    assert bounds.ylen == pytest.approx(parameters.grid.depth)
    assert bounds.zlen == pytest.approx(parameters.floor + parameters.cone_height)


def test_dish_without_cone_is_rim_height() -> None:
    parameters = replace(default_parameters(), cone_height=5.0)
    bounds = build_pixel_ring_dish(parameters)["main"].val().BoundingBox()

    assert bounds.zlen == pytest.approx(parameters.rim_height)


def test_cone_is_centred_on_its_pixel() -> None:
    parameters = default_parameters()
    model = build_pixel_ring_dish(parameters)["main"]
    x, y = parameters.grid.pixel_center((3, 4))

    top = model.faces(">Z").val().Center()

    assert top.x == pytest.approx(x, abs=1e-3)
    assert top.y == pytest.approx(y, abs=1e-3)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"cone_pixel": (0, 1)}, "interior"),
        ({"cone_base_diameter": 30}, "cone_base_diameter"),
        ({"cone_top_diameter": 20}, "cone_top_diameter"),
        ({"floor": 12}, "floor"),
        ({"pattern": ("X.", ".X")}, "corner"),
    ],
)
def test_invalid_parameters_are_rejected(
    changes: dict[str, object],
    message: str,
) -> None:
    parameters = replace(default_parameters(), **changes)

    with pytest.raises(ValueError, match=message):
        build_pixel_ring_dish(parameters)
