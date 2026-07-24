"""Tests for the display-window calibration coupon."""

import pytest

from zcad.generators.calibration.display_window_coupon import (
    DisplayWindowCouponParameters,
    build_display_window_coupon,
)


def test_display_window_coupon_is_valid() -> None:
    parameters = DisplayWindowCouponParameters()

    model = build_display_window_coupon(parameters)
    solid = model.val()
    bounds = solid.BoundingBox()

    assert solid.isValid()

    assert bounds.xlen == pytest.approx(parameters.panel_width_mm)
    assert bounds.ylen == pytest.approx(parameters.panel_depth_mm)
    assert bounds.zlen == pytest.approx(
        parameters.panel_thickness_mm + parameters.bezel_height_mm
    )


def test_display_window_coupon_has_three_openings() -> None:
    parameters = DisplayWindowCouponParameters()

    model = build_display_window_coupon(parameters)

    expected_full_panel_volume_mm3 = (
        parameters.panel_width_mm
        * parameters.panel_depth_mm
        * parameters.panel_thickness_mm
    )

    assert model.val().Volume() < (expected_full_panel_volume_mm3)


def test_custom_clearance_count_changes_width() -> None:
    parameters = DisplayWindowCouponParameters(
        clearances_mm=(
            0.1,
            0.3,
            0.5,
            0.7,
        ),
    )

    model = build_display_window_coupon(parameters)

    assert model.val().isValid()
    assert model.val().BoundingBox().xlen == pytest.approx(4 * parameters.cell_width_mm)


def test_negative_clearance_is_rejected() -> None:
    parameters = DisplayWindowCouponParameters(
        clearances_mm=(
            0.2,
            -0.1,
        ),
    )

    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        build_display_window_coupon(parameters)


def test_small_cell_is_rejected() -> None:
    parameters = DisplayWindowCouponParameters(
        cell_width_mm=20.0,
    )

    with pytest.raises(
        ValueError,
        match="does not fit",
    ):
        build_display_window_coupon(parameters)
