"""Tests for the Gridfinity socket coupon."""

import pytest

from zcad.generators.gridfinity.baseplate_socket import (
    GridfinitySocketParameters,
    build_gridfinity_socket,
)


def test_socket_is_valid() -> None:
    model = build_gridfinity_socket(GridfinitySocketParameters())

    solid = model.val()
    bounds = solid.BoundingBox()

    assert solid.isValid()
    assert solid.Volume() > 0
    assert bounds.xlen == pytest.approx(42.0)
    assert bounds.ylen == pytest.approx(42.0)
    assert bounds.zlen == pytest.approx(6.0)


@pytest.mark.parametrize(
    "parameters",
    [
        GridfinitySocketParameters(
            cells_x=0,
        ),
        GridfinitySocketParameters(
            cells_y=0,
        ),
        GridfinitySocketParameters(
            plate_thickness=0,
        ),
    ],
)
def test_invalid_socket_is_rejected(
    parameters: GridfinitySocketParameters,
) -> None:
    with pytest.raises(ValueError):
        build_gridfinity_socket(parameters)
