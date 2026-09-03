"""Tests for the tattoo-line travel case generator."""

import cadquery as cq
import pytest

from zcad.generators.travel_case import (
    TravelCaseParameters,
    build_travel_case,
)


def default_parameters() -> TravelCaseParameters:
    """Return a representative travel-case specification."""
    return TravelCaseParameters(
        width=180,
        depth=245,
        wall=3,
        floor_thickness=3,
        wall_height=100,
        corner_radius=6,
        handle_width=90,
        handle_height=25,
        handle_top_margin=15,
    )


def test_travel_case_is_valid() -> None:
    solid = build_travel_case(default_parameters()).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_bounds_match_footprint_and_wall_height() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()
    bounds = solid.BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)
    assert bounds.ylen == pytest.approx(parameters.depth + parameters.label_height)
    assert bounds.zlen == pytest.approx(
        parameters.floor_thickness + parameters.wall_height
    )


def test_interior_is_hollow() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    mid_interior_z = parameters.floor_thickness + parameters.wall_height / 2

    assert not solid.isInside(cq.Vector(0, 0, mid_interior_z))


def test_floor_is_solid() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    mid_floor_z = parameters.floor_thickness / 2

    assert solid.isInside(cq.Vector(0, 0, mid_floor_z))


def test_handles_open_through_both_end_walls() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    handle_center_z = (
        parameters.floor_thickness
        + parameters.wall_height
        - parameters.handle_top_margin
        - parameters.handle_height / 2
    )

    for sign in (-1, 1):
        y_wall = sign * (parameters.depth / 2 - parameters.wall / 2)
        assert not solid.isInside(cq.Vector(0, y_wall, handle_center_z))


def test_wall_survives_below_the_handle() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    y_wall = parameters.depth / 2 - parameters.wall / 2
    near_floor_z = parameters.floor_thickness + 3

    assert solid.isInside(cq.Vector(0, y_wall, near_floor_z))


def test_side_walls_survive_away_from_the_handles() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    handle_center_z = (
        parameters.floor_thickness
        + parameters.wall_height
        - parameters.handle_top_margin
        - parameters.handle_height / 2
    )
    x_wall = parameters.width / 2 - parameters.wall / 2

    assert solid.isInside(cq.Vector(x_wall, 0, handle_center_z))


def test_interior_fits_the_rest_of_the_line() -> None:
    """The interior must actually hold this line's other pieces: wide
    enough for the ink cap tray, deep enough for the stencil holder
    (the single largest dimension in the whole line), and tall enough
    for the stencil holder plus headroom for something stacked on it."""
    parameters = default_parameters()
    interior_width = parameters.width - 2 * parameters.wall
    interior_depth = parameters.depth - 2 * parameters.wall

    ink_cap_tray_width = 160.0
    stencil_holder_depth = 210.3
    stencil_holder_height = 48.0
    grip_stand_height = 26.0

    assert interior_width > ink_cap_tray_width
    assert interior_depth > stencil_holder_depth
    assert parameters.wall_height > stencil_holder_height + grip_stand_height


def test_strap_slots_open_through_both_side_walls() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    slot_center_z = (
        parameters.floor_thickness
        + parameters.wall_height
        - parameters.strap_slot_top_margin
        - parameters.strap_slot_height / 2
    )

    for x_wall in (
        -(parameters.width / 2 - parameters.wall / 2),
        parameters.width / 2 - parameters.wall / 2,
    ):
        for y_position in parameters.strap_positions_y():
            assert not solid.isInside(cq.Vector(x_wall, y_position, slot_center_z))


def test_side_wall_survives_between_strap_slots() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    slot_center_z = (
        parameters.floor_thickness
        + parameters.wall_height
        - parameters.strap_slot_top_margin
        - parameters.strap_slot_height / 2
    )
    x_wall = parameters.width / 2 - parameters.wall / 2

    assert solid.isInside(cq.Vector(x_wall, 0, slot_center_z))


def test_wall_survives_below_the_strap_slot() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    x_wall = parameters.width / 2 - parameters.wall / 2
    y_position = parameters.strap_positions_y()[0]
    near_floor_z = parameters.floor_thickness + 3

    assert solid.isInside(cq.Vector(x_wall, y_position, near_floor_z))


def test_strap_slots_can_be_disabled() -> None:
    parameters = TravelCaseParameters(
        width=180,
        depth=230,
        wall=3,
        floor_thickness=3,
        wall_height=100,
        strap_slots=False,
    )
    solid = build_travel_case(parameters).val()

    slot_center_z = (
        parameters.floor_thickness
        + parameters.wall_height
        - parameters.strap_slot_top_margin
        - parameters.strap_slot_height / 2
    )
    x_wall = parameters.width / 2 - parameters.wall / 2

    for y_position in parameters.strap_positions_y():
        assert solid.isInside(cq.Vector(x_wall, y_position, slot_center_z))


def test_negative_strap_count_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_travel_case(
            TravelCaseParameters(
                width=180,
                depth=230,
                strap_count=0,
            )
        )


def test_strap_slots_too_close_to_the_corner_are_rejected() -> None:
    with pytest.raises(ValueError):
        build_travel_case(
            TravelCaseParameters(
                width=180,
                depth=230,
                strap_count=2,
                strap_spacing=220,
            )
        )


def test_floor_ridge_retains_the_stencil_holder_footprint() -> None:
    """The ridge wall must be solid, and its opening must be large
    enough for the stencil holder's own 150 x 210 mm footprint."""
    parameters = default_parameters()

    assert parameters.floor_ridge_opening_width > 150.0
    assert parameters.floor_ridge_opening_depth > 210.3


def test_floor_ridge_wall_is_solid_and_opening_is_clear() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    ridge_mid_z = parameters.floor_thickness + parameters.floor_ridge_height / 2
    ridge_wall_x = (
        parameters.floor_ridge_opening_width / 2 + parameters.floor_ridge_wall / 2
    )

    assert solid.isInside(cq.Vector(ridge_wall_x, 0, ridge_mid_z))
    assert not solid.isInside(cq.Vector(0, 0, ridge_mid_z))


def test_floor_ridge_can_be_disabled() -> None:
    parameters = TravelCaseParameters(
        width=180,
        depth=245,
        wall=3,
        floor_thickness=3,
        wall_height=100,
        floor_ridge=False,
    )
    solid = build_travel_case(parameters).val()

    ridge_mid_z = parameters.floor_thickness + parameters.floor_ridge_height / 2
    ridge_wall_x = (
        parameters.floor_ridge_opening_width / 2 + parameters.floor_ridge_wall / 2
    )

    assert not solid.isInside(cq.Vector(ridge_wall_x, 0, ridge_mid_z))


def test_oversized_floor_ridge_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_travel_case(
            TravelCaseParameters(
                width=180,
                depth=245,
                floor_ridge_opening_width=200,
            )
        )


def test_tray_ledges_are_solid_and_interior_stays_clear() -> None:
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    ledge_mid_z = parameters.tray_ledge_height - parameters.tray_ledge_thickness / 2
    ledge_x = (
        parameters.width / 2 - parameters.wall - parameters.tray_ledge_protrusion / 2
    )

    assert solid.isInside(cq.Vector(ledge_x, 0, ledge_mid_z))
    assert not solid.isInside(cq.Vector(0, 0, ledge_mid_z))


def test_tray_ledge_can_be_disabled() -> None:
    parameters = TravelCaseParameters(
        width=180,
        depth=245,
        wall=3,
        floor_thickness=3,
        wall_height=100,
        tray_ledge=False,
    )
    solid = build_travel_case(parameters).val()

    ledge_mid_z = parameters.tray_ledge_height - parameters.tray_ledge_thickness / 2
    ledge_x = (
        parameters.width / 2 - parameters.wall - parameters.tray_ledge_protrusion / 2
    )

    assert not solid.isInside(cq.Vector(ledge_x, 0, ledge_mid_z))


def test_tray_ledge_below_floor_ridge_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_travel_case(
            TravelCaseParameters(
                width=180,
                depth=245,
                tray_ledge_height=5,
            )
        )


def test_pack_order_labels_build_successfully() -> None:
    solid = build_travel_case(default_parameters()).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_pack_order_labels_can_be_disabled() -> None:
    parameters = TravelCaseParameters(
        width=180,
        depth=245,
        wall=3,
        floor_thickness=3,
        wall_height=100,
        pack_order_labels=False,
    )
    solid = build_travel_case(parameters).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_ledge_center_x_matches_the_actual_ledge_position() -> None:
    """The label-placement helper must agree with where the ledge
    itself is actually built, or the '2' would float in open space."""
    parameters = default_parameters()
    solid = build_travel_case(parameters).val()

    ledge_mid_z = parameters.tray_ledge_height - parameters.tray_ledge_thickness / 2
    center_x = parameters.ledge_center_x(1)

    assert solid.isInside(cq.Vector(center_x, 0, ledge_mid_z))


def test_oversized_floor_label_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_travel_case(
            TravelCaseParameters(
                width=180,
                depth=245,
                pack_order_floor_label_size=200,
            )
        )


def test_oversized_ledge_label_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_travel_case(
            TravelCaseParameters(
                width=180,
                depth=245,
                pack_order_ledge_label_size=20,
            )
        )


def test_invalid_travel_case_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_travel_case(
            TravelCaseParameters(
                width=10,
                depth=170,
                wall=3,
            )
        )


def test_oversized_handle_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_travel_case(
            TravelCaseParameters(
                width=230,
                depth=170,
                handle_width=225,
            )
        )


def test_handle_too_close_to_top_or_floor_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_travel_case(
            TravelCaseParameters(
                width=230,
                depth=170,
                wall_height=90,
                handle_height=25,
                handle_top_margin=60,
            )
        )
