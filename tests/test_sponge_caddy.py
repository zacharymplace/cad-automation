"""Tests for the sink-edge sponge-and-brush caddy generator."""

import cadquery as cq
import pytest

from zcad.generators.sponge_caddy import (
    SpongeCaddyParameters,
    build_sponge_caddy,
)


def default_parameters() -> SpongeCaddyParameters:
    """Return a representative sponge-caddy specification."""
    return SpongeCaddyParameters(
        width=150,
        depth=100,
        wall=3,
        basin_height=16,
        floor_back=6,
        floor_front=2.6,
        spout_length=30,
        spout_tip_thickness=1.4,
        spout_flare_margin=15,
        corner_radius=5,
        rack_thickness=3,
        sponge_slot_length=80,
        sponge_slot_width=18,
        sponge_slot_center_x=-40,
        brush_hole_diameter=30,
        brush_hole_count=2,
        brush_hole_spacing=38,
        brush_holes_center_x=40,
    )


def test_sponge_caddy_returns_basin_and_rack() -> None:
    parts = build_sponge_caddy(default_parameters())

    assert set(parts) == {"basin", "rack"}


def test_sponge_caddy_parts_are_valid() -> None:
    parts = build_sponge_caddy(default_parameters())

    for model in parts.values():
        assert model.val().isValid()
        assert model.val().Volume() > 0


def test_rack_bounds_match_basin_footprint() -> None:
    parameters = default_parameters()
    parts = build_sponge_caddy(parameters)

    bounds = parts["rack"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)
    assert bounds.ylen == pytest.approx(parameters.depth)
    assert bounds.zlen == pytest.approx(parameters.rack_thickness)


def test_sponge_slot_is_open_through_the_rack() -> None:
    """The slot must be a clean through-cut: empty at the slot center,
    solid just outside it on either side."""
    parameters = default_parameters()
    rack = build_sponge_caddy(parameters)["rack"].val()

    mid_z = parameters.rack_thickness / 2
    slot_x = parameters.sponge_slot_center_x
    edge_offset = parameters.sponge_slot_width / 2 + 1.0

    assert not rack.isInside(cq.Vector(slot_x, 0, mid_z))
    assert rack.isInside(cq.Vector(slot_x - edge_offset, 0, mid_z))
    assert rack.isInside(cq.Vector(slot_x + edge_offset, 0, mid_z))


def test_brush_holes_are_open_through_the_rack() -> None:
    parameters = default_parameters()
    rack = build_sponge_caddy(parameters)["rack"].val()
    mid_z = parameters.rack_thickness / 2

    for x, y in parameters.brush_hole_positions():
        assert not rack.isInside(cq.Vector(x, y, mid_z))


def test_drainage_holes_avoid_slot_and_brush_holes() -> None:
    """Drainage holes filling the rest of the plate must not land on
    top of the slot or brush holes (which would just be wasted cuts,
    or worse, leave razor-thin webs at the boundary)."""
    parameters = default_parameters()
    rack = build_sponge_caddy(parameters)["rack"].val()
    mid_z = parameters.rack_thickness / 2

    # A point just past the slot's edge, mid-slot in Y, should be solid
    # plate material (part of a web), not accidentally hollowed out.
    edge_x = parameters.sponge_slot_center_x + parameters.sponge_slot_width / 2 + 1.5
    assert rack.isInside(cq.Vector(edge_x, 0, mid_z))


def test_basin_matches_drainage_basin_bounds() -> None:
    """The shared basin must behave identically to the one drip_tray
    uses -- same sloped floor, same flaring spout."""
    parameters = default_parameters()
    parts = build_sponge_caddy(parameters)
    bounds = parts["basin"].val().BoundingBox()

    interior_width = parameters.width - 2 * parameters.wall
    tip_width = interior_width + 2 * parameters.spout_flare_margin

    assert bounds.xlen == pytest.approx(max(parameters.width, tip_width))
    assert bounds.ylen == pytest.approx(
        parameters.depth + parameters.spout_length + parameters.label_height
    )
    assert bounds.zlen == pytest.approx(parameters.basin_height)


def test_invalid_sponge_caddy_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_sponge_caddy(
            SpongeCaddyParameters(
                width=150,
                depth=100,
                sponge_slot_center_x=0,
                brush_holes_center_x=5,
            )
        )
