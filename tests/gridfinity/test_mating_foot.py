"""Tests for Gridfinity mating-foot geometry."""

import pytest

from zcad.generators.gridfinity.mating_foot import (
    GridfinityMatingFootParameters,
    build_gridfinity_mating_foot,
)


def test_single_mating_foot_is_valid() -> None:
    model = build_gridfinity_mating_foot(GridfinityMatingFootParameters())

    solid = model.val()
    bounds = solid.BoundingBox()

    assert solid.isValid()
    assert solid.Volume() > 0
    assert bounds.zlen == pytest.approx(4.75)


def test_two_by_one_uses_grid_pitch() -> None:
    model = build_gridfinity_mating_foot(
        GridfinityMatingFootParameters(
            cells_x=2,
            cells_y=1,
        )
    )

    bounds = model.val().BoundingBox()

    assert bounds.xlen > 70
    assert bounds.ylen < 42


@pytest.mark.parametrize(
    "parameters",
    [
        GridfinityMatingFootParameters(
            cells_x=0,
        ),
        GridfinityMatingFootParameters(
            cells_y=0,
        ),
    ],
)
def test_invalid_mating_foot_is_rejected(
    parameters: GridfinityMatingFootParameters,
) -> None:
    with pytest.raises(ValueError):
        build_gridfinity_mating_foot(parameters)
