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
        spout_flare_margin=15,
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


def test_basin_bounds_include_spout_overhang_and_flare() -> None:
    parameters = default_parameters()
    parts = build_drip_tray(parameters)

    bounds = parts["basin"].val().BoundingBox()
    interior_width = parameters.width - 2 * parameters.wall
    tip_width = interior_width + 2 * parameters.spout_flare_margin

    assert bounds.xlen == pytest.approx(max(parameters.width, tip_width))
    assert bounds.ylen == pytest.approx(
        parameters.depth + parameters.spout_length + parameters.label_height
    )
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


def test_spout_flares_wider_than_the_basin_opening() -> None:
    """A point beyond the basin's interior half-width must be empty near
    the basin opening but solid near the spout tip, proving the spout
    actually widens rather than just overhanging at a constant width."""
    parameters = default_parameters()
    basin = build_drip_tray(parameters)["basin"].val()

    interior_half_width = (parameters.width - 2 * parameters.wall) / 2
    probe_x = interior_half_width + parameters.spout_flare_margin / 2

    near_front_y = parameters.depth / 2 + 1
    near_tip_y = parameters.depth / 2 + parameters.spout_length - 3

    outside_flare_at_front = basin.isInside(cq.Vector(probe_x, near_front_y, 0.5))
    inside_flare_near_tip = basin.isInside(cq.Vector(probe_x, near_tip_y, 0.2))

    assert not outside_flare_at_front
    assert inside_flare_near_tip


def test_spout_tip_bulge_reaches_further_at_the_corners() -> None:
    """A round or oval sink's cutout is closest to the tray at the
    centerline and curves away at the sides, so the tip should reach
    further at its corners than at its centerline (concave/swallow-tail),
    not the other way around."""
    parameters = DripTrayParameters(
        width=115,
        depth=100,
        spout_length=28,
        spout_flare_margin=15,
        spout_tip_bulge=14,
    )
    basin = build_drip_tray(parameters)["basin"].val()

    tip_y = parameters.depth / 2 + parameters.spout_length
    half_width = (parameters.width - 2 * parameters.wall + 2 * 15) / 2
    # 0.8 * half_width, partway up the bulge: inside the wing but clear of
    # the wingtip fillet, so the probe isn't accidentally rounded away.
    near_corner_x = half_width * 0.8
    partway_up_bulge = tip_y + parameters.spout_tip_bulge * 0.4

    corner_reaches_bulge = basin.isInside(cq.Vector(near_corner_x, partway_up_bulge, 0.2))
    center_does_not_reach_bulge = not basin.isInside(
        cq.Vector(0, tip_y + parameters.spout_tip_bulge - 2, 0.2)
    )

    assert corner_reaches_bulge
    assert center_does_not_reach_bulge


def test_house_mark_is_raised_on_the_back_wall() -> None:
    """The default label should protrude past the exterior back face."""
    parameters = default_parameters()
    parts = build_drip_tray(parameters)

    bounds = parts["basin"].val().BoundingBox()

    assert bounds.ymin == pytest.approx(-parameters.depth / 2 - parameters.label_height)


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
