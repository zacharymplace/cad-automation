import pytest

from zcad.generators.gridfinity.specification import (
    GridfinitySpecification,
)


def test_single_cell_width() -> None:
    spec = GridfinitySpecification()

    assert spec.cell_width(1) == pytest.approx(41.5)


def test_double_cell_width() -> None:
    spec = GridfinitySpecification()

    assert spec.cell_width(2) == pytest.approx(83.5)


def test_invalid_cells() -> None:
    spec = GridfinitySpecification()

    with pytest.raises(ValueError):
        spec.cell_width(0)
