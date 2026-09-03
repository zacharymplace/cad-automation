"""Tests for the tattoo-station stencil/transfer paper holder."""

import cadquery as cq
import pytest

from zcad.generators.stencil_holder import (
    StencilHolderParameters,
    build_stencil_holder,
)


def default_parameters() -> StencilHolderParameters:
    """Return a representative stencil-holder specification."""
    return StencilHolderParameters(
        width=150,
        depth=210,
        wall=3,
        floor_thickness=3,
        corner_radius=5,
        back_wall_height=45,
        side_wall_height=20,
        front_wall_height=8,
        thumb_notch=True,
        thumb_notch_width=30,
    )


def test_stencil_holder_is_valid() -> None:
    solid = build_stencil_holder(default_parameters()).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_bounds_match_footprint_and_tallest_wall() -> None:
    parameters = default_parameters()
    solid = build_stencil_holder(parameters).val()
    bounds = solid.BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)
    assert bounds.ylen == pytest.approx(parameters.depth + parameters.label_height)
    assert bounds.zlen == pytest.approx(
        parameters.floor_thickness + parameters.back_wall_height
    )


def test_back_wall_is_taller_than_front_wall() -> None:
    """A point at side-wall height above the floor should be solid at
    the back wall but open at the front wall's low lip."""
    parameters = default_parameters()
    solid = build_stencil_holder(parameters).val()

    mid_height_z = parameters.floor_thickness + parameters.side_wall_height

    back_y = parameters.depth / 2 - parameters.wall / 2
    front_y = -parameters.depth / 2 + parameters.wall / 2

    assert solid.isInside(cq.Vector(0, back_y, mid_height_z))
    assert not solid.isInside(cq.Vector(0, front_y, mid_height_z))


def test_thumb_notch_opens_the_front_wall_to_the_floor() -> None:
    parameters = default_parameters()
    solid = build_stencil_holder(parameters).val()

    front_y = -parameters.depth / 2 + parameters.wall / 2
    near_floor_z = parameters.floor_thickness + 0.1

    assert not solid.isInside(cq.Vector(0, front_y, near_floor_z))


def test_front_wall_survives_beside_the_notch() -> None:
    """Outside the notch's width, the front wall should still be
    solid material, not cut away."""
    parameters = default_parameters()
    solid = build_stencil_holder(parameters).val()

    front_y = -parameters.depth / 2 + parameters.wall / 2
    mid_front_wall_z = parameters.floor_thickness + parameters.front_wall_height / 2
    beside_notch_x = parameters.thumb_notch_width / 2 + 3

    assert solid.isInside(cq.Vector(beside_notch_x, front_y, mid_front_wall_z))


def test_floor_spans_the_full_footprint() -> None:
    parameters = default_parameters()
    solid = build_stencil_holder(parameters).val()

    mid_floor_z = parameters.floor_thickness / 2
    corner_x = parameters.width / 2 - parameters.wall
    corner_y = parameters.depth / 2 - parameters.wall

    assert solid.isInside(cq.Vector(corner_x, corner_y, mid_floor_z))


def test_thumb_notch_can_be_disabled() -> None:
    parameters = StencilHolderParameters(
        width=150,
        depth=210,
        wall=3,
        floor_thickness=3,
        back_wall_height=45,
        side_wall_height=20,
        front_wall_height=8,
        thumb_notch=False,
    )
    solid = build_stencil_holder(parameters).val()

    front_y = -parameters.depth / 2 + parameters.wall / 2
    near_floor_z = parameters.floor_thickness + 0.1

    assert solid.isInside(cq.Vector(0, front_y, near_floor_z))


def divided_parameters() -> StencilHolderParameters:
    """A holder split into three compartments by two dividers."""
    return StencilHolderParameters(
        width=150,
        depth=210,
        wall=3,
        floor_thickness=3,
        corner_radius=5,
        back_wall_height=45,
        side_wall_height=20,
        front_wall_height=8,
        thumb_notch=True,
        thumb_notch_width=30,
        divider_count=2,
        divider_height=20,
    )


def test_compartments_and_dividers_are_ordered_and_counted() -> None:
    parameters = divided_parameters()
    compartments = parameters.compartment_centers_x()
    dividers = parameters.divider_centers_x()

    assert len(compartments) == parameters.divider_count + 1
    assert len(dividers) == parameters.divider_count
    assert compartments == sorted(compartments)
    assert dividers == sorted(dividers)

    for i, divider_x in enumerate(dividers):
        assert compartments[i] < divider_x < compartments[i + 1]


def test_divided_holder_is_valid() -> None:
    solid = build_stencil_holder(divided_parameters()).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_dividers_separate_the_compartments() -> None:
    """A divider must actually be solid material between compartments,
    not just an empty gap."""
    parameters = divided_parameters()
    solid = build_stencil_holder(parameters).val()

    divider_x = parameters.divider_centers_x()[0]
    mid_divider_z = parameters.floor_thickness + parameters.divider_height / 2

    assert solid.isInside(cq.Vector(divider_x, 0, mid_divider_z))


def test_each_compartment_gets_its_own_notch() -> None:
    parameters = divided_parameters()
    solid = build_stencil_holder(parameters).val()

    front_y = -parameters.depth / 2 + parameters.wall / 2
    near_floor_z = parameters.floor_thickness + 0.1

    for center_x in parameters.compartment_centers_x():
        assert not solid.isInside(cq.Vector(center_x, front_y, near_floor_z))


def test_compartment_labels_build_successfully() -> None:
    solid = build_stencil_holder(divided_parameters()).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_compartment_labels_can_be_disabled() -> None:
    parameters = StencilHolderParameters(
        width=150,
        depth=210,
        wall=3,
        floor_thickness=3,
        back_wall_height=45,
        side_wall_height=20,
        front_wall_height=8,
        divider_count=2,
        compartment_labels=False,
    )
    solid = build_stencil_holder(parameters).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_compartment_labels_are_ignored_without_dividers() -> None:
    """No dividers means one compartment -- a number would be
    meaningless clutter, so it should be skipped even though
    compartment_labels defaults to True."""
    parameters = default_parameters()
    bounds_with_default = build_stencil_holder(parameters).val().BoundingBox()

    explicit_off = StencilHolderParameters(
        width=parameters.width,
        depth=parameters.depth,
        wall=parameters.wall,
        floor_thickness=parameters.floor_thickness,
        corner_radius=parameters.corner_radius,
        back_wall_height=parameters.back_wall_height,
        side_wall_height=parameters.side_wall_height,
        front_wall_height=parameters.front_wall_height,
        thumb_notch=parameters.thumb_notch,
        thumb_notch_width=parameters.thumb_notch_width,
        compartment_labels=False,
    )
    bounds_explicit_off = build_stencil_holder(explicit_off).val().BoundingBox()

    assert bounds_with_default.zlen == pytest.approx(bounds_explicit_off.zlen)


def test_oversized_compartment_label_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_stencil_holder(
            StencilHolderParameters(
                width=150,
                depth=210,
                wall=3,
                divider_count=2,
                compartment_label_size=50,
            )
        )


def test_negative_divider_count_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_stencil_holder(
            StencilHolderParameters(
                width=150,
                depth=210,
                divider_count=-1,
            )
        )


def test_too_many_dividers_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_stencil_holder(
            StencilHolderParameters(
                width=150,
                depth=210,
                wall=3,
                divider_count=30,
            )
        )


def test_notch_too_wide_for_divided_compartments_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_stencil_holder(
            StencilHolderParameters(
                width=150,
                depth=210,
                wall=3,
                divider_count=2,
                thumb_notch_width=50,
            )
        )


def test_invalid_stencil_holder_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_stencil_holder(
            StencilHolderParameters(
                width=10,
                depth=210,
                wall=3,
            )
        )


def test_oversized_thumb_notch_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_stencil_holder(
            StencilHolderParameters(
                width=150,
                depth=210,
                thumb_notch_width=200,
            )
        )
