"""Tests for the tattoo-machine grip stand generator."""

import cadquery as cq
import pytest

from zcad.generators.grip_stand import (
    GripStandParameters,
    build_grip_stand,
)


def default_parameters() -> GripStandParameters:
    """Return a representative grip-stand specification."""
    return GripStandParameters(
        base_width=60,
        base_depth=95,
        base_height=6,
        corner_radius=4,
        grip_diameter=25,
        grip_hole_clearance=1.0,
        ridge_height=20,
        ridge_block_width=40,
        ridge_block_length=16,
        notch_spacing=55,
        notch_side_wall=4,
        notch_wall_min=2,
        base_edge_margin=8,
    )


def test_grip_stand_is_valid() -> None:
    model = build_grip_stand(default_parameters())
    solid = model.val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_grip_stand_bounds_match_base_and_ridge() -> None:
    parameters = default_parameters()
    solid = build_grip_stand(parameters).val()
    bounds = solid.BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.base_width)
    assert bounds.ylen == pytest.approx(parameters.base_depth + parameters.label_height)
    assert bounds.zlen == pytest.approx(
        parameters.base_height + parameters.ridge_height
    )


def test_notches_are_open_at_the_grip_diameter() -> None:
    """Directly above each notch's centerline, at the ridge top, the
    grip's cross-section should be open, not solid material."""
    parameters = default_parameters()
    stand = build_grip_stand(parameters).val()

    groove_z = parameters.base_height + parameters.ridge_height

    for center_y in parameters.notch_centers_y():
        assert not stand.isInside(cq.Vector(0, center_y, groove_z - 0.1))


def test_notches_leave_material_below_the_groove() -> None:
    """The half-cylinder notch must not cut all the way down through
    the ridge into the base plate."""
    parameters = default_parameters()
    stand = build_grip_stand(parameters).val()

    groove_z = parameters.base_height + parameters.ridge_height
    grip_radius = parameters.grip_hole_diameter / 2
    below_groove_z = groove_z - grip_radius - parameters.notch_wall_min / 2

    for center_y in parameters.notch_centers_y():
        assert stand.isInside(cq.Vector(0, center_y, below_groove_z))


def test_material_survives_between_the_two_notches() -> None:
    """The gap between the front and back notch blocks should not be
    solid all the way down -- only the two blocks are raised."""
    parameters = default_parameters()
    stand = build_grip_stand(parameters).val()

    above_base_z = parameters.base_height + 0.5

    assert not stand.isInside(cq.Vector(0, 0, above_base_z))


def test_base_plate_is_present_under_both_notches() -> None:
    parameters = default_parameters()
    stand = build_grip_stand(parameters).val()

    mid_base_z = parameters.base_height / 2

    for center_y in parameters.notch_centers_y():
        assert stand.isInside(cq.Vector(0, center_y, mid_base_z))


def gang_mounted_parameters() -> GripStandParameters:
    """A wider base holding two side-by-side machine lanes."""
    return GripStandParameters(
        base_width=120,
        base_depth=95,
        base_height=6,
        corner_radius=4,
        grip_diameter=25,
        grip_hole_clearance=1.0,
        ridge_height=20,
        ridge_block_width=40,
        ridge_block_length=16,
        notch_spacing=55,
        notch_side_wall=4,
        notch_wall_min=2,
        base_edge_margin=8,
        machine_count=2,
        machine_pitch=50,
    )


def test_single_machine_lane_defaults_to_center() -> None:
    parameters = default_parameters()

    assert parameters.lane_centers_x() == [0.0]


def test_multiple_machine_lanes_are_symmetric_and_spaced() -> None:
    parameters = gang_mounted_parameters()
    lanes = parameters.lane_centers_x()

    assert len(lanes) == parameters.machine_count
    assert lanes == sorted(lanes)
    assert sum(lanes) == pytest.approx(0.0)
    assert lanes[1] - lanes[0] == pytest.approx(parameters.machine_pitch)


def test_gang_mounted_stand_is_valid() -> None:
    solid = build_grip_stand(gang_mounted_parameters()).val()

    assert solid.isValid()
    assert solid.Volume() > 0


def test_gang_mounted_notches_are_all_open() -> None:
    parameters = gang_mounted_parameters()
    stand = build_grip_stand(parameters).val()

    groove_z = parameters.base_height + parameters.ridge_height

    for lane_x in parameters.lane_centers_x():
        for center_y in parameters.notch_centers_y():
            assert not stand.isInside(cq.Vector(lane_x, center_y, groove_z - 0.1))


def test_gang_mounted_lanes_do_not_merge() -> None:
    """Solid base material should survive between two adjacent lanes'
    ridge blocks -- they must not overlap or fuse into one mass."""
    parameters = gang_mounted_parameters()
    stand = build_grip_stand(parameters).val()

    lanes = parameters.lane_centers_x()
    midpoint_x = (lanes[0] + lanes[1]) / 2
    above_base_z = parameters.base_height + 0.5

    assert not stand.isInside(cq.Vector(midpoint_x, 0, above_base_z))


def test_invalid_machine_count_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_grip_stand(
            GripStandParameters(
                machine_count=0,
            )
        )


def test_undersized_machine_pitch_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_grip_stand(
            GripStandParameters(
                base_width=120,
                ridge_block_width=40,
                machine_count=2,
                machine_pitch=30,
            )
        )


def test_undersized_base_width_for_gang_mount_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_grip_stand(
            GripStandParameters(
                base_width=60,
                ridge_block_width=40,
                machine_count=2,
                machine_pitch=50,
            )
        )


def test_invalid_grip_stand_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_grip_stand(
            GripStandParameters(
                notch_spacing=10,
                ridge_block_length=16,
            )
        )


def test_undersized_ridge_height_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_grip_stand(
            GripStandParameters(
                grip_diameter=25,
                ridge_height=5,
            )
        )


def test_undersized_base_depth_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_grip_stand(
            GripStandParameters(
                base_depth=40,
                notch_spacing=55,
                ridge_block_length=16,
            )
        )
