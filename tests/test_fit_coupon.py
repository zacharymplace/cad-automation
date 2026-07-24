"""Tests for the peg-and-socket fit coupon."""

import pytest

from zcad.generators.fit_coupon import (
    FitCouponParameters,
    build_fit_coupon,
)


def test_fit_coupon_is_valid() -> None:
    parameters = FitCouponParameters(
        nominal_diameter=8.0,
        clearances=[
            0.0,
            0.1,
            0.2,
            0.3,
            0.4,
        ],
    )

    model = build_fit_coupon(parameters)
    solid = model.val()
    bounds = solid.BoundingBox()

    assert solid.isValid()
    assert solid.Volume() > 0
    assert bounds.xlen == pytest.approx(110)
    assert bounds.ylen == pytest.approx(66)
    assert bounds.zlen == pytest.approx(15)


@pytest.mark.parametrize(
    "parameters",
    [
        FitCouponParameters(
            nominal_diameter=0,
            clearances=[0.2],
        ),
        FitCouponParameters(
            nominal_diameter=8,
            clearances=[],
        ),
        FitCouponParameters(
            nominal_diameter=8,
            clearances=[-0.1],
        ),
        FitCouponParameters(
            nominal_diameter=8,
            clearances=[0.2, 0.2],
        ),
    ],
)
def test_invalid_fit_coupon_is_rejected(
    parameters: FitCouponParameters,
) -> None:
    with pytest.raises(ValueError):
        build_fit_coupon(parameters)
