"""Tests for the Gridfinity-inspired empty bin."""

import pytest

from zcad.generators.gridfinity.bin import (
    GridfinityBinParameters,
    build_gridfinity_bin,
)


def test_one_by_one_bin_is_valid() -> None:
    model = build_gridfinity_bin(
        GridfinityBinParameters(
            cells_x=1,
            cells_y=1,
            height_units=3,
        )
    )

    solid = model.val()
    bounds = solid.BoundingBox()

    assert solid.isValid()
    assert solid.Volume() > 0
    assert bounds.xlen == pytest.approx(41.5)
    assert bounds.ylen == pytest.approx(41.5)
    assert bounds.zlen == pytest.approx(21.0)


@pytest.mark.parametrize(
    "parameters",
    [
        GridfinityBinParameters(0, 1, 3),
        GridfinityBinParameters(1, 0, 3),
        GridfinityBinParameters(1, 1, 0),
        GridfinityBinParameters(
            1,
            1,
            3,
            wall=0,
        ),
        GridfinityBinParameters(
            1,
            1,
            3,
            floor=0,
        ),
    ],
)
def test_invalid_bin_is_rejected(
    parameters: GridfinityBinParameters,
) -> None:
    with pytest.raises(ValueError):
        build_gridfinity_bin(parameters)
