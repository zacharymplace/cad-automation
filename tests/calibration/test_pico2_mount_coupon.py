"""Tests for the Raspberry Pi Pico 2 mount coupon."""

import cadquery as cq
import pytest
from zcad_core.hardware import (
    get_raspberry_pi_pico2,
)

from zcad.generators.calibration.pico2_mount_coupon import (
    Pico2MountCouponParameters,
    build_pico2_mount_coupon,
)


def test_coupon_is_valid() -> None:
    parameters = Pico2MountCouponParameters()
    model = build_pico2_mount_coupon(parameters)
    solid = model.val()
    board = get_raspberry_pi_pico2()

    assert isinstance(model, cq.Workplane)
    assert solid.isValid()
    assert solid.Volume() > 0

    bounds = solid.BoundingBox()

    assert bounds.xlen == pytest.approx(
        board.board_width_mm + (2 * parameters.board_edge_clearance_mm)
    )
    assert bounds.ylen == pytest.approx(
        board.board_length_mm + (2 * parameters.board_edge_clearance_mm)
    )
    assert bounds.zlen == pytest.approx(
        parameters.base_height_mm + board.recommended_standoff_height_mm
    )


def test_coupon_accepts_mount_overrides() -> None:
    model = build_pico2_mount_coupon(
        Pico2MountCouponParameters(
            standoff_height_mm=4.0,
            mounting_hole_clearance_mm=0.2,
        )
    )

    assert model.val().isValid()
    assert model.val().BoundingBox().zlen == pytest.approx(6.0)


def test_coupon_rejects_invalid_clearance() -> None:
    parameters = Pico2MountCouponParameters(
        mounting_hole_clearance_mm=-0.1,
    )

    with pytest.raises(
        ValueError,
        match="mounting_hole_clearance_mm",
    ):
        build_pico2_mount_coupon(parameters)
