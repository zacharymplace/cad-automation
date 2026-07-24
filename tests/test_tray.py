import pytest

from zcad.generators.tray import (
    TrayParameters,
    build_tray,
)


def test_tray_geometry() -> None:
    model = build_tray(
        TrayParameters(
            width=120,
            depth=80,
            height=30,
            wall=3,
            floor=3,
            corner_radius=5,
        )
    )

    solid = model.val()
    bounds = solid.BoundingBox()

    assert solid.isValid()
    assert solid.Volume() > 0
    assert bounds.xlen == pytest.approx(120)
    assert bounds.ylen == pytest.approx(80)
    assert bounds.zlen == pytest.approx(30)


def test_invalid_tray_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_tray(
            TrayParameters(
                width=5,
                depth=80,
                height=30,
                wall=3,
            )
        )
