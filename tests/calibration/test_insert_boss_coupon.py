"""Tests for insert-boss calibration coupon."""

import cadquery as cq
import pytest

from zcad.generators.calibration.insert_boss_coupon import (
    InsertBossCouponParameters,
    build_insert_boss_coupon,
)


def test_coupon_is_valid() -> None:
    model = build_insert_boss_coupon(
        InsertBossCouponParameters(),
    )

    solid = model.val()

    assert isinstance(model, cq.Workplane)
    assert solid.isValid()
    assert solid.Volume() > 0
    assert solid.BoundingBox().xlen == pytest.approx(120.0)
