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


def test_height_units() -> None:
    spec = GridfinitySpecification()

    assert spec.height(1) == pytest.approx(7.0)
    assert spec.height(3) == pytest.approx(21.0)


def test_verified_constants() -> None:
    spec = GridfinitySpecification()

    assert spec.profile_corner_radius == pytest.approx(4.0)
    assert spec.bin_mating_depth == pytest.approx(4.75)
    assert spec.baseplate_mating_depth == pytest.approx(4.4)
    assert spec.bottom_chamfer == pytest.approx(0.8)
    assert spec.magnet_diameter == pytest.approx(6.0)
    assert spec.magnet_depth == pytest.approx(2.0)
    assert spec.magnet_center_inset == pytest.approx(8.0)
    assert spec.screw_size == "M3"


def test_invalid_inputs() -> None:
    spec = GridfinitySpecification()

    with pytest.raises(ValueError):
        spec.cell_width(0)

    with pytest.raises(ValueError):
        spec.height(0)
