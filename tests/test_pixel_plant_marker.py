"""Tests for the pixel plant marker."""

from dataclasses import replace

import cadquery as cq
import pytest

from zcad.generators.pixel_plant_marker import (
    PixelPlantMarkerParameters,
    build_pixel_plant_marker,
)


def default_parameters() -> PixelPlantMarkerParameters:
    """Label disabled so most tests skip text tessellation."""
    return PixelPlantMarkerParameters(
        pixel_size=5,
        thickness=3,
        groove_depth=0.5,
        groove_width=0.8,
        band_width=44,
        band_height=14,
        band_corner_radius=2,
        label="",
        stake_length=110,
        stake_top_width=16,
        stake_tip_width=3,
    )


def test_returns_single_valid_solid() -> None:
    parts = build_pixel_plant_marker(default_parameters())

    assert set(parts) == {"main"}
    model = parts["main"]
    assert model.val().isValid()
    assert len(model.solids().vals()) == 1


def test_bounds_span_icon_band_and_stake() -> None:
    parameters = default_parameters()
    bounds = build_pixel_plant_marker(parameters)["main"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.total_width)
    assert bounds.ylen == pytest.approx(parameters.total_height)
    assert bounds.zlen == pytest.approx(parameters.thickness)


def test_label_adds_raised_text() -> None:
    plain = default_parameters()
    labelled = replace(plain, label="BASIL")

    plain_volume = build_pixel_plant_marker(plain)["main"].val().Volume()
    labelled_model = build_pixel_plant_marker(labelled)["main"]

    assert labelled_model.val().Volume() > plain_volume
    assert labelled_model.val().BoundingBox().zlen == pytest.approx(
        plain.thickness + plain.label_height
    )


def test_stake_tapers_to_its_tip() -> None:
    parameters = default_parameters()
    model = build_pixel_plant_marker(parameters)["main"]
    tip_y = parameters.stake_top_y - parameters.stake_length

    slab = cq.Workplane("XY").box(200, 1.0, 20).translate((0, tip_y + 0.5, 0))
    near_tip = model.intersect(slab).val().BoundingBox()

    assert model.val().BoundingBox().ymin == pytest.approx(tip_y)
    assert near_tip.xlen < parameters.stake_top_width / 2


def test_icon_face_is_scored_into_tiles() -> None:
    parameters = default_parameters()
    smooth = replace(parameters, groove_depth=0.0)

    scored = build_pixel_plant_marker(parameters)["main"].val().Volume()
    plain = build_pixel_plant_marker(smooth)["main"].val().Volume()

    assert scored < plain


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"stake_tip_width": 20}, "stake_tip_width"),
        ({"stake_top_width": 60}, "stake_top_width"),
        ({"pattern": (".XX.", "XXXX", "....")}, "bottom row"),
        ({"pattern": ("XXXXXXXXXXXX",), "band_width": 20}, "wider than band_width"),
        ({"label": "BASIL", "label_size": 14}, "band_height"),
        ({"label": "A VERY LONG CROP NAME INDEED"}, "band_width"),
    ],
)
def test_invalid_parameters_are_rejected(
    changes: dict[str, object],
    message: str,
) -> None:
    parameters = replace(default_parameters(), **changes)

    with pytest.raises(ValueError, match=message):
        build_pixel_plant_marker(parameters)
