"""Tests for the home-bar garnish caddy generator."""

import cadquery as cq
import pytest

from zcad.generators.garnish_caddy import (
    GarnishCaddyParameters,
    build_garnish_caddy,
)


def default_parameters() -> GarnishCaddyParameters:
    """Return a representative garnish-caddy specification."""
    return GarnishCaddyParameters(
        width=220,
        depth=80,
        wall=3,
        floor_thickness=3,
        wall_height=35,
        corner_radius=6,
        compartment_count=4,
        thumb_notch=True,
        thumb_notch_width=25,
    )


def test_garnish_caddy_is_valid() -> None:
    solid = build_garnish_caddy(default_parameters()).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_bounds_match_footprint_and_wall_height() -> None:
    parameters = default_parameters()
    bounds = build_garnish_caddy(parameters).val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)
    assert bounds.ylen == pytest.approx(parameters.depth + parameters.label_height)
    assert bounds.zlen == pytest.approx(
        parameters.floor_thickness + parameters.wall_height
    )


def test_compartments_and_dividers_are_ordered_and_counted() -> None:
    parameters = default_parameters()
    compartments = parameters.compartment_centers_x()
    dividers = parameters.divider_centers_x()

    assert len(compartments) == parameters.compartment_count
    assert len(dividers) == parameters.compartment_count - 1
    assert compartments == sorted(compartments)
    assert dividers == sorted(dividers)

    for i, divider_x in enumerate(dividers):
        assert compartments[i] < divider_x < compartments[i + 1]


def test_dividers_separate_the_compartments() -> None:
    """A divider must actually be solid material between compartments,
    not just an empty gap."""
    parameters = default_parameters()
    solid = build_garnish_caddy(parameters).val()

    mid_z = parameters.floor_thickness + parameters.wall_height / 2

    for divider_x in parameters.divider_centers_x():
        assert solid.isInside(cq.Vector(divider_x, 0, mid_z))


def test_compartments_are_open() -> None:
    parameters = default_parameters()
    solid = build_garnish_caddy(parameters).val()

    mid_z = parameters.floor_thickness + parameters.wall_height / 2

    for center_x in parameters.compartment_centers_x():
        assert not solid.isInside(cq.Vector(center_x, 0, mid_z))


def test_thumb_notch_cuts_fully_through_the_end_wall() -> None:
    """A real bug caught during design: the first pass only cut
    partway through the wall, since the cutter was centered on the
    wall's outer face instead of its midpoint."""
    parameters = default_parameters()
    solid = build_garnish_caddy(parameters).val()

    mid_z = parameters.floor_thickness + parameters.wall_height / 2
    outer_face_x = -parameters.width / 2 + 0.1
    inner_face_x = -parameters.width / 2 + parameters.wall - 0.1

    assert not solid.isInside(cq.Vector(outer_face_x, 0, mid_z))
    assert not solid.isInside(cq.Vector(inner_face_x, 0, mid_z))


def test_wall_survives_beside_the_notch() -> None:
    parameters = default_parameters()
    solid = build_garnish_caddy(parameters).val()

    mid_z = parameters.floor_thickness + parameters.wall_height / 2
    outer_face_x = -parameters.width / 2 + 0.1
    beside_notch_y = parameters.thumb_notch_width / 2 + 3

    assert solid.isInside(cq.Vector(outer_face_x, beside_notch_y, mid_z))


def test_thumb_notch_can_be_disabled() -> None:
    parameters = GarnishCaddyParameters(
        width=220,
        depth=80,
        wall=3,
        floor_thickness=3,
        wall_height=35,
        thumb_notch=False,
    )
    solid = build_garnish_caddy(parameters).val()

    mid_z = parameters.floor_thickness + parameters.wall_height / 2
    outer_face_x = -parameters.width / 2 + 0.1

    assert solid.isInside(cq.Vector(outer_face_x, 0, mid_z))


def test_compartment_labels_build_successfully() -> None:
    solid = build_garnish_caddy(default_parameters()).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_compartment_labels_can_be_disabled() -> None:
    parameters = GarnishCaddyParameters(
        width=220,
        depth=80,
        compartment_count=4,
        compartment_labels=False,
    )
    solid = build_garnish_caddy(parameters).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_single_compartment_skips_labels_by_default() -> None:
    """One compartment doesn't need a number -- it's the only option."""
    parameters = GarnishCaddyParameters(
        width=220,
        depth=80,
        compartment_count=1,
    )
    with_default_labels = build_garnish_caddy(parameters).val().BoundingBox()

    explicit_off = GarnishCaddyParameters(
        width=220,
        depth=80,
        compartment_count=1,
        compartment_labels=False,
    )
    without_labels = build_garnish_caddy(explicit_off).val().BoundingBox()

    assert with_default_labels.zlen == pytest.approx(without_labels.zlen)


def test_invalid_garnish_caddy_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_garnish_caddy(
            GarnishCaddyParameters(
                width=10,
                depth=80,
            )
        )


def test_too_many_compartments_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_garnish_caddy(
            GarnishCaddyParameters(
                width=220,
                depth=80,
                compartment_count=50,
            )
        )


def test_oversized_thumb_notch_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_garnish_caddy(
            GarnishCaddyParameters(
                width=220,
                depth=80,
                thumb_notch_width=100,
            )
        )


def test_variable_compartment_widths_are_ordered_and_solid() -> None:
    """A wider compartment for citrus next to narrower ones for olives
    and cherry stems -- the compartments and their dividers must still
    line up correctly and stay open/solid as expected."""
    parameters = GarnishCaddyParameters(
        width=220,
        depth=80,
        wall=3,
        floor_thickness=3,
        wall_height=35,
        compartment_count=4,
        compartment_widths=(70, 45, 45, 45),
        thumb_notch=False,
    )
    solid = build_garnish_caddy(parameters).val()

    compartments = parameters.compartment_centers_x()
    dividers = parameters.divider_centers_x()

    assert len(compartments) == 4
    assert len(dividers) == 3
    assert compartments == sorted(compartments)
    assert dividers == sorted(dividers)

    for i, divider_x in enumerate(dividers):
        assert compartments[i] < divider_x < compartments[i + 1]

    mid_z = parameters.floor_thickness + parameters.wall_height / 2

    for center_x in compartments:
        assert not solid.isInside(cq.Vector(center_x, 0, mid_z))

    for divider_x in dividers:
        assert solid.isInside(cq.Vector(divider_x, 0, mid_z))


def test_variable_compartment_widths_span_the_interior() -> None:
    parameters = GarnishCaddyParameters(
        width=220,
        depth=80,
        wall=3,
        compartment_count=4,
        compartment_widths=(70, 45, 45, 45),
    )

    interior_width = parameters.width - 2 * parameters.wall
    dividers_width = (parameters.compartment_count - 1) * parameters.wall

    assert sum(parameters.compartment_widths) + dividers_width == pytest.approx(
        interior_width
    )


def test_mismatched_compartment_widths_length_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_garnish_caddy(
            GarnishCaddyParameters(
                width=220,
                depth=80,
                compartment_count=4,
                compartment_widths=(70, 45, 45),
            )
        )


def test_oversized_compartment_widths_sum_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_garnish_caddy(
            GarnishCaddyParameters(
                width=220,
                depth=80,
                compartment_count=4,
                compartment_widths=(70, 45, 45, 100),
            )
        )
