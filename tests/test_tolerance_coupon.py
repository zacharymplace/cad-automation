"""Tests for the tolerance coupon generator."""

import pytest

from zcad.generators.tolerance_coupon import (
    ToleranceCouponParameters,
    build_tolerance_coupon,
)


def test_tolerance_coupon_is_valid() -> None:
    parameters = ToleranceCouponParameters(
        hole_diameters=[
            2.8,
            3.0,
            3.2,
            3.4,
            3.6,
        ],
        slot_widths=[
            2.8,
            3.0,
            3.2,
            3.4,
            3.6,
        ],
    )

    model = build_tolerance_coupon(parameters)
    solid = model.val()
    bounds = solid.BoundingBox()

    assert solid.isValid()
    assert solid.Volume() > 0
    assert bounds.xlen == pytest.approx(100)
    assert bounds.ylen == pytest.approx(46)
    assert bounds.zlen > 4.0
    assert bounds.zlen < 4.8


@pytest.mark.parametrize(
    "parameters",
    [
        ToleranceCouponParameters(
            hole_diameters=[],
            slot_widths=[3.0],
        ),
        ToleranceCouponParameters(
            hole_diameters=[3.0],
            slot_widths=[],
        ),
        ToleranceCouponParameters(
            hole_diameters=[-3.0],
            slot_widths=[3.0],
        ),
        ToleranceCouponParameters(
            hole_diameters=[20.0],
            slot_widths=[3.0],
        ),
    ],
)
def test_invalid_coupon_is_rejected(
    parameters: ToleranceCouponParameters,
) -> None:
    with pytest.raises(ValueError):
        build_tolerance_coupon(parameters)
