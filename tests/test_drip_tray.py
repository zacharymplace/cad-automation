"""Tests for the soap-dispenser drip tray generator."""

import cadquery as cq
import pytest

from zcad.generators.drip_tray import (
    DripTrayParameters,
    build_drip_tray,
)


def default_parameters() -> DripTrayParameters:
    """Return a representative drip-tray specification."""
    return DripTrayParameters(
        width=115,
        depth=100,
        wall=3,
        basin_height=14,
        floor_back=5,
        floor_front=2.4,
        spout_length=28,
        spout_tip_thickness=1.4,
        corner_radius=5,
        grid_thickness=3,
        grid_hole_diameter=6,
        grid_hole_spacing=12,
        grid_edge_margin=8,
    )


def test_drip_tray_returns_basin_and_grid() -> None:
    parts = build_drip_tray(default_parameters())

    assert set(parts) == {"basin", "grid"}


def test_drip_tray_parts_are_valid() -> None:
    parts = build_drip_tray(default_parameters())

    for model in parts.values():
        assert model.val().isValid()
        assert model.val().Volume() > 0


def test_basin_bounds_include_spout_overhang() -> None:
    parameters = default_parameters()
    parts = build_drip_tray(parameters)

    bounds = parts["basin"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)
    assert bounds.ylen == pytest.approx(parameters.depth + parameters.spout_length)
    assert bounds.zlen == pytest.approx(parameters.basin_height)


def test_grid_bounds_match_basin_footprint() -> None:
    parameters = default_parameters()
    parts = build_drip_tray(parameters)

    bounds = parts["grid"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)
    assert bounds.ylen == pytest.approx(parameters.depth)
    assert bounds.zlen == pytest.approx(parameters.grid_thickness)


def test_floor_slopes_down_toward_spout() -> None:
    """The basin floor must be solid below its taper and open above it,
    at both the back wall and the spout tip, so drips are guided
    downhill toward the sink instead of pooling."""
    parameters = default_parameters()
    basin = build_drip_tray(parameters)["basin"].val()

    back_y = -parameters.depth / 2 + parameters.wall + 5
    tip_y = parameters.depth / 2 + parameters.spout_length - 3

    below_back_floor = basin.isInside(cq.Vector(0, back_y, parameters.floor_back - 1))
    above_back_floor = basin.isInside(cq.Vector(0, back_y, parameters.floor_back + 2))
    below_tip = basin.isInside(
        cq.Vector(0, tip_y, parameters.spout_tip_thickness - 0.5)
    )
    above_tip = basin.isInside(cq.Vector(0, tip_y, parameters.spout_tip_thickness + 1))

    assert below_back_floor
    assert not above_back_floor
    assert below_tip
    assert not above_tip


def test_invalid_drip_tray_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_drip_tray(
            DripTrayParameters(
                width=115,
                depth=100,
                floor_back=2.0,
                floor_front=2.4,
            )
        )
