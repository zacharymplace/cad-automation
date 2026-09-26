"""Tests for the pixel block planter."""

from dataclasses import replace

import cadquery as cq
import pytest

from zcad.generators.pixel_block_planter import (
    PixelBlockPlanterParameters,
    build_pixel_block_planter,
)


def default_parameters() -> PixelBlockPlanterParameters:
    return PixelBlockPlanterParameters(
        pixel_size=10,
        face_pixels=8,
        wall=2.4,
        floor=3,
        relief_depth=1.0,
        pixel_inset=0.2,
        drain_hole_diameter=6,
    )


def test_returns_single_valid_solid() -> None:
    parts = build_pixel_block_planter(default_parameters())

    assert set(parts) == {"main"}
    model = parts["main"]
    assert model.val().isValid()
    assert len(model.solids().vals()) == 1


def test_block_is_a_cube_of_face_pixels() -> None:
    parameters = default_parameters()
    bounds = build_pixel_block_planter(parameters)["main"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.size)
    assert bounds.ylen == pytest.approx(parameters.size)
    assert bounds.zlen == pytest.approx(parameters.size)


def test_front_relief_is_recessed_into_front_wall_only() -> None:
    """Sample a filled creeper pixel (an eye) and an empty one on the
    front wall, and the same spot on the back wall."""
    parameters = default_parameters()
    model = build_pixel_block_planter(parameters)["main"]
    grid = parameters.front_grid
    half = parameters.size / 2
    probe_depth = half - parameters.relief_depth / 2

    eye_x, eye_v = grid.pixel_center((2, 1))
    blank_x, blank_v = grid.pixel_center((0, 0))

    eye_point = cq.Vector(eye_x, -probe_depth, half + eye_v)
    blank_point = cq.Vector(blank_x, -probe_depth, half + blank_v)
    back_point = cq.Vector(eye_x, probe_depth, half + eye_v)

    assert not model.val().isInside(eye_point)
    assert model.val().isInside(blank_point)
    assert model.val().isInside(back_point)


def test_side_pattern_recesses_other_three_walls() -> None:
    plain = default_parameters()
    sided = replace(plain, side_pattern=("XX", "XX"))

    plain_volume = build_pixel_block_planter(plain)["main"].val().Volume()
    sided_volume = build_pixel_block_planter(sided)["main"].val().Volume()

    tile = plain.pixel_size - 2 * plain.pixel_inset
    expected_removed = 3 * 4 * tile * tile * plain.relief_depth

    assert plain_volume - sided_volume == pytest.approx(expected_removed, rel=1e-3)


def test_block_is_hollow() -> None:
    parameters = default_parameters()
    volume = build_pixel_block_planter(parameters)["main"].val().Volume()

    assert 0 < volume < 0.3 * parameters.size**3


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"relief_depth": 1.5}, "relief_depth"),
        ({"face_pixels": 1}, "face_pixels"),
        ({"front_pattern": ("XXXXXXXXXX",)}, "does not fit"),
        ({"drain_hole_diameter": 80}, "drain_hole_diameter"),
        ({"pixel_inset": 6}, "pixel_inset"),
    ],
)
def test_invalid_parameters_are_rejected(
    changes: dict[str, object],
    message: str,
) -> None:
    parameters = replace(default_parameters(), **changes)

    with pytest.raises(ValueError, match=message):
        build_pixel_block_planter(parameters)
