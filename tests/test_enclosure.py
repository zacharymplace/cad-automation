"""Tests for the electronics enclosure generator."""

import pytest

from zcad.generators.enclosure import (
    EnclosureParameters,
    build_enclosure,
)


def default_parameters() -> EnclosureParameters:
    """Return a representative enclosure specification."""
    return EnclosureParameters(
        width=100,
        depth=70,
        height=30,
        wall=3,
        floor=3,
        lid_thickness=3,
        lid_clearance=0.25,
        lid_lip_height=4,
        lid_lip_wall=2,
        corner_radius=4,
        cable_slot_width=14,
        cable_slot_height=8,
        mounting_hole_diameter=3.2,
        mounting_hole_spacing_x=60,
        mounting_hole_spacing_y=35,
        label="Z$ ELECTRONICS",
        label_size=6,
        label_height=0.6,
    )


def test_enclosure_returns_body_and_lid() -> None:
    parts = build_enclosure(default_parameters())

    assert set(parts) == {
        "body",
        "lid",
    }


def test_enclosure_parts_are_valid() -> None:
    parts = build_enclosure(default_parameters())

    for model in parts.values():
        assert model.val().isValid()
        assert model.val().Volume() > 0


def test_body_dimensions_match_specification() -> None:
    parts = build_enclosure(default_parameters())

    bounds = parts["body"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(100)
    assert bounds.ylen == pytest.approx(70)
    assert bounds.zlen == pytest.approx(30)


def test_lid_contains_plate_lip_and_label() -> None:
    parts = build_enclosure(default_parameters())

    bounds = parts["lid"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(100)
    assert bounds.ylen == pytest.approx(70)
    assert bounds.zlen > 7
    assert bounds.zlen < 8


@pytest.mark.parametrize(
    "parameters",
    [
        EnclosureParameters(
            width=5,
            depth=70,
            height=30,
            wall=3,
        ),
        EnclosureParameters(
            width=100,
            depth=5,
            height=30,
            wall=3,
        ),
        EnclosureParameters(
            width=100,
            depth=70,
            height=3,
            floor=3,
        ),
        EnclosureParameters(
            width=100,
            depth=70,
            height=30,
            lid_clearance=-0.1,
        ),
        EnclosureParameters(
            width=100,
            depth=70,
            height=30,
            cable_slot_width=100,
        ),
    ],
)
def test_invalid_enclosure_is_rejected(
    parameters: EnclosureParameters,
) -> None:
    with pytest.raises(ValueError):
        build_enclosure(parameters)
