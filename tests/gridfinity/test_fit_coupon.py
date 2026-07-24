"""Tests for the Gridfinity compatibility coupon."""

import pytest

from zcad.generators.gridfinity.fit_coupon import (
    GridfinityFitCouponParameters,
    build_gridfinity_fit_coupon,
)


def test_fit_coupon_returns_two_parts() -> None:
    parts = build_gridfinity_fit_coupon(GridfinityFitCouponParameters())

    assert set(parts) == {
        "foot",
        "socket",
    }


def test_fit_coupon_parts_are_valid() -> None:
    parts = build_gridfinity_fit_coupon(GridfinityFitCouponParameters())

    for model in parts.values():
        assert model.val().isValid()
        assert model.val().Volume() > 0


def test_socket_dimensions() -> None:
    parts = build_gridfinity_fit_coupon(GridfinityFitCouponParameters())

    bounds = parts["socket"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(42.0)
    assert bounds.ylen == pytest.approx(42.0)
    assert bounds.zlen == pytest.approx(6.0)


def test_invalid_coupon_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_gridfinity_fit_coupon(GridfinityFitCouponParameters(plate_thickness=0))
