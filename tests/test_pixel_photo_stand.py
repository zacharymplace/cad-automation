"""Tests for the pixel photo stand."""

import math
from dataclasses import replace

import cadquery as cq
import pytest

from zcad.generators.pixel_photo_stand import (
    PixelPhotoStandParameters,
    build_pixel_photo_stand,
)


def default_parameters() -> PixelPhotoStandParameters:
    return PixelPhotoStandParameters(
        pixel_size=10,
        height=14,
        groove_depth=0.5,
        groove_width=0.8,
        slot_width=2.6,
        slot_depth=9,
        slot_tilt_degrees=12,
        slot_offset_y=5,
    )


def test_returns_single_valid_solid() -> None:
    parts = build_pixel_photo_stand(default_parameters())

    assert set(parts) == {"main"}
    model = parts["main"]
    assert model.val().isValid()
    assert len(model.solids().vals()) == 1


def test_bounds_match_outline_and_height() -> None:
    parameters = default_parameters()
    bounds = build_pixel_photo_stand(parameters)["main"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.grid.width)
    assert bounds.ylen == pytest.approx(parameters.grid.depth)
    assert bounds.zlen == pytest.approx(parameters.height)


def test_slot_is_open_at_top_and_leans_back() -> None:
    parameters = default_parameters()
    model = build_pixel_photo_stand(parameters)["main"].val()
    floor_z = parameters.height - parameters.slot_depth
    y0 = parameters.slot_offset_y

    # Just above the slot floor the void is at the offset; near the top it
    # has drifted toward +Y by depth * tan(tilt).
    drift = (parameters.slot_depth - 1.0) * math.tan(
        math.radians(parameters.slot_tilt_degrees)
    )

    assert not model.isInside(cq.Vector(0.0, y0, floor_z + 0.5))
    assert not model.isInside(cq.Vector(0.0, y0 + drift, parameters.height - 0.5))
    assert model.isInside(cq.Vector(0.0, y0, floor_z - 0.5))
    assert model.isInside(cq.Vector(0.0, y0 - 3.0, parameters.height - 0.5))


def test_slot_removes_material() -> None:
    parameters = default_parameters()
    shallow = replace(parameters, slot_depth=4.0)

    deep_volume = build_pixel_photo_stand(parameters)["main"].val().Volume()
    shallow_volume = build_pixel_photo_stand(shallow)["main"].val().Volume()

    assert deep_volume < shallow_volume


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"slot_depth": 12}, "slot_depth"),
        ({"slot_tilt_degrees": 45}, "slot_tilt_degrees"),
        ({"slot_offset_y": 30}, "slot_offset_y"),
        ({"pattern": ("X.X",)}, "connected"),
    ],
)
def test_invalid_parameters_are_rejected(
    changes: dict[str, object],
    message: str,
) -> None:
    parameters = replace(default_parameters(), **changes)

    with pytest.raises(ValueError, match=message):
        build_pixel_photo_stand(parameters)
