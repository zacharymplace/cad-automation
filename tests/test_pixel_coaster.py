"""Tests for the pixel coaster."""

from dataclasses import replace

import pytest

from zcad.generators.pixel_coaster import (
    PixelCoasterParameters,
    build_pixel_coaster,
)


def default_parameters() -> PixelCoasterParameters:
    return PixelCoasterParameters(
        size=92,
        thickness=5,
        corner_radius=6,
        rim_width=5,
        recess_depth=1.2,
        pixel_size=5,
        pixel_inset=0.25,
    )


def test_returns_single_valid_solid() -> None:
    parts = build_pixel_coaster(default_parameters())

    assert set(parts) == {"main"}
    model = parts["main"]
    assert model.val().isValid()
    assert len(model.solids().vals()) == 1


def test_relief_is_flush_with_rim() -> None:
    parameters = default_parameters()
    bounds = build_pixel_coaster(parameters)["main"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.size)
    assert bounds.ylen == pytest.approx(parameters.size)
    assert bounds.zlen == pytest.approx(parameters.thickness)


def test_recess_removes_more_than_relief_returns() -> None:
    parameters = default_parameters()
    volume = build_pixel_coaster(parameters)["main"].val().Volume()
    slab = parameters.size**2 * parameters.thickness

    assert volume < slab


def test_disconnected_patterns_are_allowed() -> None:
    """Islands are fine for a relief; the gamepad buttons rely on it."""
    parameters = replace(default_parameters(), pattern=("X.X", "...", "X.X"))
    model = build_pixel_coaster(parameters)["main"]

    assert model.val().isValid()
    assert len(model.solids().vals()) == 1


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"recess_depth": 4.5}, "recess_depth"),
        ({"rim_width": 50}, "rim_width"),
        ({"pixel_size": 8}, "does not fit"),
        ({"pixel_inset": 3}, "pixel_inset"),
        ({"pattern": ("X", "XX")}, "same length"),
    ],
)
def test_invalid_parameters_are_rejected(
    changes: dict[str, object],
    message: str,
) -> None:
    parameters = replace(default_parameters(), **changes)

    with pytest.raises(ValueError, match=message):
        build_pixel_coaster(parameters)
