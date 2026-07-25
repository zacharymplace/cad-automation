"""Tests for edge-directed enclosure cable slots."""

import cadquery as cq
import pytest

from zcad.generators.enclosure import (
    EnclosureParameters,
    build_enclosure,
)


def _parameters(
    *,
    edge: str,
    center_offset: float = 0.0,
    bottom_offset: float = 2.0,
) -> EnclosureParameters:
    return EnclosureParameters(
        width=80.0,
        depth=60.0,
        height=30.0,
        wall=3.0,
        floor=3.0,
        corner_radius=0.0,
        cable_slot_width=12.0,
        cable_slot_height=6.0,
        cable_slot_edge=edge,
        cable_slot_center_offset=center_offset,
        cable_slot_bottom_offset=bottom_offset,
        mounting_hole_spacing_x=50.0,
        mounting_hole_spacing_y=30.0,
    )


def _wall_probe_points(
    parameters: EnclosureParameters,
) -> tuple[cq.Vector, cq.Vector]:
    z = (
        -parameters.height / 2
        + parameters.floor
        + parameters.cable_slot_bottom_offset
        + parameters.cable_slot_height / 2
    )

    x_wall = parameters.width / 2 - parameters.wall / 2
    y_wall = parameters.depth / 2 - parameters.wall / 2
    offset = parameters.cable_slot_center_offset

    if parameters.cable_slot_edge == "negative_y":
        return (
            cq.Vector(offset, -y_wall, z),
            cq.Vector(offset, y_wall, z),
        )

    if parameters.cable_slot_edge == "positive_y":
        return (
            cq.Vector(offset, y_wall, z),
            cq.Vector(offset, -y_wall, z),
        )

    if parameters.cable_slot_edge == "negative_x":
        return (
            cq.Vector(-x_wall, offset, z),
            cq.Vector(x_wall, offset, z),
        )

    return (
        cq.Vector(x_wall, offset, z),
        cq.Vector(-x_wall, offset, z),
    )


@pytest.mark.parametrize(
    "edge",
    [
        "negative_y",
        "positive_y",
        "negative_x",
        "positive_x",
    ],
)
def test_cable_slot_is_cut_on_requested_edge_only(
    edge: str,
) -> None:
    parameters = _parameters(
        edge=edge,
        center_offset=4.0,
    )
    body = build_enclosure(parameters)["body"].val()

    requested_probe, opposite_probe = _wall_probe_points(parameters)

    assert body.isValid()
    assert body.Volume() > 0

    assert not body.isInside(
        requested_probe,
        tolerance=1e-6,
    )
    assert body.isInside(
        opposite_probe,
        tolerance=1e-6,
    )


def test_cable_slot_bottom_offset_controls_height() -> None:
    low = _parameters(
        edge="negative_y",
        bottom_offset=1.0,
    )
    high = _parameters(
        edge="negative_y",
        bottom_offset=7.0,
    )

    low_body = build_enclosure(low)["body"].val()
    high_body = build_enclosure(high)["body"].val()

    low_requested, _ = _wall_probe_points(low)
    high_requested, _ = _wall_probe_points(high)

    assert not low_body.isInside(
        low_requested,
        tolerance=1e-6,
    )
    assert high_body.isInside(
        low_requested,
        tolerance=1e-6,
    )

    assert not high_body.isInside(
        high_requested,
        tolerance=1e-6,
    )
    assert low_body.isInside(
        high_requested,
        tolerance=1e-6,
    )


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (
            {
                "cable_slot_edge": "diagonal",
            },
            "unsupported cable_slot_edge",
        ),
        (
            {
                "cable_slot_bottom_offset": -0.1,
            },
            "cable_slot_bottom_offset",
        ),
        (
            {
                "cable_slot_center_offset": 40.0,
            },
            "cable_slot_center_offset",
        ),
        (
            {
                "cable_slot_bottom_offset": 20.0,
                "cable_slot_height": 8.0,
            },
            "cavity height",
        ),
    ],
)
def test_invalid_cable_slot_policy_is_rejected(
    arguments: dict[str, object],
    message: str,
) -> None:
    parameters = EnclosureParameters(
        width=80.0,
        depth=60.0,
        height=30.0,
        wall=3.0,
        floor=3.0,
        corner_radius=0.0,
        mounting_hole_spacing_x=50.0,
        mounting_hole_spacing_y=30.0,
        **arguments,
    )

    with pytest.raises(
        ValueError,
        match=message,
    ):
        build_enclosure(parameters)
