"""Tests for the adjustable phone/tablet stand generator."""

import pytest

from zcad.generators.phone_stand import (
    PhoneStandParameters,
    build_phone_stand,
)


def default_parameters() -> PhoneStandParameters:
    """Return a representative phone-stand specification."""
    return PhoneStandParameters(
        device_width=80,
        device_thickness=12,
        base_width=100,
        base_depth=75,
        base_wall=4,
        slot_offset=40,
        slot_wall=3,
        slot_height=12,
        slot_clearance=2,
        cradle_width=100,
        cradle_height=80,
        cradle_wall=4,
        corner_radius=4,
        knuckle_count=5,
        knuckle_diameter=10,
        knuckle_length=14,
        knuckle_gap=0.6,
        pin_hole_diameter=4,
        pin_diameter=4.2,
        pin_margin=3,
    )


def test_phone_stand_returns_base_cradle_and_pin() -> None:
    parts = build_phone_stand(default_parameters())

    assert set(parts) == {"base", "cradle", "pin"}


def test_phone_stand_parts_are_valid() -> None:
    parts = build_phone_stand(default_parameters())

    for model in parts.values():
        assert model.val().isValid()
        assert model.val().Volume() > 0


def test_base_bounds_match_footprint() -> None:
    """The hinge knuckles are half-cylinders centered on the back
    (Y=0) edge, so they overhang the plate by one knuckle radius."""
    parameters = default_parameters()
    base = build_phone_stand(parameters)["base"].val()
    bounds = base.BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.base_width)
    assert bounds.ylen == pytest.approx(
        parameters.base_depth + parameters.knuckle_radius
    )


def test_cradle_bounds_match_footprint() -> None:
    parameters = default_parameters()
    cradle = build_phone_stand(parameters)["cradle"].val()
    bounds = cradle.BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.cradle_width)
    assert bounds.ylen == pytest.approx(
        parameters.cradle_height + parameters.knuckle_radius
    )


def test_pin_length_spans_hinge_with_margin() -> None:
    parameters = default_parameters()
    pin = build_phone_stand(parameters)["pin"].val()
    bounds = pin.BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.pin_length())
    assert bounds.xlen == pytest.approx(
        parameters.total_hinge_width() + 2 * parameters.pin_margin
    )


def test_hinge_segments_alternate_and_do_not_overlap() -> None:
    parameters = default_parameters()
    segments = parameters.hinge_segments()

    assert len(segments) == parameters.knuckle_count
    assert segments[0][2] == "base"
    assert segments[-1][2] == "base"

    for index, (start, end, owner) in enumerate(segments):
        assert end > start
        assert owner == ("base" if index % 2 == 0 else "cradle")

        if index > 0:
            previous_end = segments[index - 1][1]
            assert start >= previous_end - 1e-9


def test_device_slot_is_open_between_the_walls() -> None:
    """The device slot must be a clean gap: solid at each wall, empty
    in the channel between them."""
    import cadquery as cq

    parameters = default_parameters()
    base = build_phone_stand(parameters)["base"].val()

    mid_z = parameters.base_wall + parameters.slot_height / 2
    near_wall_mid = parameters.slot_offset + parameters.slot_wall / 2
    channel_mid = (
        parameters.slot_offset + parameters.slot_wall + parameters.slot_width / 2
    )

    assert base.isInside(cq.Vector(0, near_wall_mid, mid_z))
    assert not base.isInside(cq.Vector(0, channel_mid, mid_z))


def test_pin_hole_is_clear_through_base_knuckles() -> None:
    import cadquery as cq

    parameters = default_parameters()
    base = build_phone_stand(parameters)["base"].val()

    axis_z = parameters.base_wall + parameters.knuckle_radius
    base_segment = next(
        segment for segment in parameters.hinge_segments() if segment[2] == "base"
    )
    segment_mid_x = (base_segment[0] + base_segment[1]) / 2

    assert not base.isInside(cq.Vector(segment_mid_x, 0, axis_z))


def test_invalid_pin_clearance_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_phone_stand(
            PhoneStandParameters(
                device_width=80,
                device_thickness=12,
                pin_hole_diameter=4,
                pin_diameter=6,
            )
        )


def test_invalid_knuckle_count_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_phone_stand(
            PhoneStandParameters(
                device_width=80,
                device_thickness=12,
                knuckle_count=4,
            )
        )


def test_oversized_hinge_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_phone_stand(
            PhoneStandParameters(
                device_width=80,
                device_thickness=12,
                base_width=40,
                cradle_width=40,
                knuckle_count=9,
                knuckle_length=14,
            )
        )
