"""Tests for the tattoo-station ink cap tray generator."""

from itertools import pairwise

import cadquery as cq
import pytest

from zcad.generators.ink_cap_tray import (
    InkCapTrayParameters,
    build_ink_cap_tray,
)


def default_parameters() -> InkCapTrayParameters:
    """Return a representative standalone ink-cap-tray specification."""
    return InkCapTrayParameters(
        width=160,
        depth=90,
        wall=3,
        basin_height=16,
        standalone_floor=3,
        corner_radius=5,
        rack_thickness=4,
        rack_edge_margin=10,
        cap_diameter=13,
        cap_hole_clearance=0.4,
        cap_count=6,
        cap_spacing=20,
    )


def sink_edge_parameters() -> InkCapTrayParameters:
    """Return the sink-adjacent variant that drains over a spout."""
    return InkCapTrayParameters(
        width=160,
        depth=90,
        wall=3,
        basin_height=16,
        floor_back=6,
        floor_front=2.6,
        spout_length=30,
        spout_tip_thickness=1.4,
        spout_flare_margin=15,
        corner_radius=5,
        rack_thickness=4,
        rack_edge_margin=10,
        cap_diameter=13,
        cap_hole_clearance=0.4,
        cap_count=6,
        cap_spacing=20,
        basin_style="sink_edge",
    )


def test_ink_cap_tray_returns_basin_and_rack() -> None:
    parts = build_ink_cap_tray(default_parameters())

    assert set(parts) == {"basin", "rack"}


def test_ink_cap_tray_parts_are_valid() -> None:
    for parameters in (default_parameters(), sink_edge_parameters()):
        parts = build_ink_cap_tray(parameters)

        for model in parts.values():
            assert model.val().isValid()
            assert model.val().Volume() > 0


def test_rack_bounds_match_basin_footprint() -> None:
    parameters = default_parameters()
    parts = build_ink_cap_tray(parameters)

    bounds = parts["rack"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)
    assert bounds.ylen == pytest.approx(parameters.depth)
    assert bounds.zlen == pytest.approx(
        parameters.rack_thickness + parameters.cap_label_height
    )


def test_cap_holes_are_open_through_the_rack() -> None:
    parameters = default_parameters()
    rack = build_ink_cap_tray(parameters)["rack"].val()
    mid_z = parameters.rack_thickness / 2

    for x, y in parameters.cap_positions():
        assert not rack.isInside(cq.Vector(x, y, mid_z))


def test_cap_holes_are_evenly_spaced_and_centered() -> None:
    parameters = default_parameters()
    positions = parameters.cap_positions()

    assert len(positions) == parameters.cap_count

    xs = [x for x, _y in positions]
    assert xs == sorted(xs)
    assert sum(xs) == pytest.approx(0.0)

    spacings = [b - a for a, b in pairwise(xs)]
    for spacing in spacings:
        assert spacing == pytest.approx(parameters.cap_spacing)


def test_material_between_adjacent_holes_survives() -> None:
    """Adjacent cap holes must not merge into one slot -- there should
    be solid rack material at the midpoint between two holes."""
    parameters = default_parameters()
    rack = build_ink_cap_tray(parameters)["rack"].val()
    mid_z = parameters.rack_thickness / 2

    positions = parameters.cap_positions()
    midpoint_x = (positions[0][0] + positions[1][0]) / 2

    assert rack.isInside(cq.Vector(midpoint_x, 0, mid_z))


def test_cap_hole_chamfer_widens_only_near_the_top() -> None:
    """The countersink should widen the hole's mouth near the rack's
    top face, while the bore stays straight through the rest of the
    thickness."""
    parameters = default_parameters()
    rack = build_ink_cap_tray(parameters)["rack"].val()

    x0, y0 = parameters.cap_positions()[0]
    hole_radius = parameters.cap_hole_diameter / 2
    test_x = x0 + hole_radius + 0.3

    mid_z = parameters.rack_thickness / 2
    near_top_z = parameters.rack_thickness - parameters.cap_hole_chamfer / 2

    assert rack.isInside(cq.Vector(test_x, y0, mid_z))
    assert not rack.isInside(cq.Vector(test_x, y0, near_top_z))


def test_cap_hole_chamfer_can_be_disabled() -> None:
    parameters = InkCapTrayParameters(
        width=160,
        depth=90,
        wall=3,
        basin_height=16,
        standalone_floor=3,
        rack_thickness=4,
        cap_diameter=13,
        cap_hole_clearance=0.4,
        cap_count=6,
        cap_spacing=20,
        cap_hole_chamfer=0,
    )
    rack = build_ink_cap_tray(parameters)["rack"].val()

    x0, y0 = parameters.cap_positions()[0]
    hole_radius = parameters.cap_hole_diameter / 2
    test_x = x0 + hole_radius + 0.3
    near_top_z = parameters.rack_thickness - 0.2

    assert rack.isInside(cq.Vector(test_x, y0, near_top_z))


def test_cap_labels_raise_the_rack_top_face() -> None:
    parameters = InkCapTrayParameters(
        width=160,
        depth=90,
        wall=3,
        basin_height=16,
        standalone_floor=3,
        rack_thickness=4,
        cap_diameter=13,
        cap_hole_clearance=0.4,
        cap_count=6,
        cap_spacing=20,
        cap_labels=False,
    )
    rack = build_ink_cap_tray(parameters)["rack"].val()
    bounds = rack.BoundingBox()

    assert bounds.zlen == pytest.approx(parameters.rack_thickness)


def test_foot_pockets_recess_the_underside_without_puncturing() -> None:
    """The pocket should hollow out the bottom of the floor without
    reaching all the way through into the basin cavity above it."""
    parameters = default_parameters()
    basin = build_ink_cap_tray(parameters)["basin"].val()

    foot_x = parameters.width / 2 - parameters.foot_inset
    foot_y = parameters.depth / 2 - parameters.foot_inset
    inside_pocket_z = parameters.foot_depth / 2
    above_pocket_z = (parameters.foot_depth + parameters.standalone_floor) / 2

    assert not basin.isInside(cq.Vector(foot_x, foot_y, inside_pocket_z))
    assert basin.isInside(cq.Vector(foot_x, foot_y, above_pocket_z))


def test_foot_pockets_can_be_disabled() -> None:
    parameters = InkCapTrayParameters(
        width=160,
        depth=90,
        wall=3,
        basin_height=16,
        standalone_floor=3,
        foot_pockets=False,
    )
    basin = build_ink_cap_tray(parameters)["basin"].val()

    foot_x = parameters.width / 2 - parameters.foot_inset
    foot_y = parameters.depth / 2 - parameters.foot_inset
    inside_pocket_z = parameters.foot_depth / 2

    assert basin.isInside(cq.Vector(foot_x, foot_y, inside_pocket_z))


def test_foot_depth_deeper_than_floor_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_ink_cap_tray(
            InkCapTrayParameters(
                width=160,
                depth=90,
                standalone_floor=3,
                foot_depth=3,
            )
        )


def mixing_well_parameters() -> InkCapTrayParameters:
    """A wider tray with the small-cap row plus two larger mixing
    wells appended past it."""
    return InkCapTrayParameters(
        width=320,
        depth=90,
        wall=3,
        basin_height=16,
        standalone_floor=3,
        corner_radius=5,
        rack_thickness=4,
        rack_edge_margin=10,
        cap_diameter=13,
        cap_hole_clearance=0.4,
        cap_count=6,
        cap_spacing=20,
        mixing_well_count=2,
    )


def test_mixing_wells_are_disabled_by_default() -> None:
    parameters = default_parameters()

    assert parameters.mixing_well_positions() == []
    assert len(parameters.hole_positions()) == parameters.cap_count


def test_mixing_wells_extend_past_the_small_cap_row() -> None:
    parameters = mixing_well_parameters()
    positions = parameters.hole_positions()

    assert len(positions) == parameters.cap_count + parameters.mixing_well_count

    row_max_x = max(x for x, _y in parameters.cap_positions())
    mixing_xs = [x for x, _y in parameters.mixing_well_positions()]

    assert all(x > row_max_x for x in mixing_xs)
    assert mixing_xs == sorted(mixing_xs)


def test_mixing_wells_are_open_through_the_rack() -> None:
    parameters = mixing_well_parameters()
    rack = build_ink_cap_tray(parameters)["rack"].val()
    mid_z = parameters.rack_thickness / 2

    for x, y in parameters.mixing_well_positions():
        assert not rack.isInside(cq.Vector(x, y, mid_z))


def test_mixing_wells_parts_are_valid() -> None:
    parts = build_ink_cap_tray(mixing_well_parameters())

    for model in parts.values():
        assert model.val().isValid()
        assert model.val().Volume() > 0


def test_negative_mixing_well_count_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_ink_cap_tray(
            InkCapTrayParameters(
                width=260,
                depth=90,
                mixing_well_count=-1,
            )
        )


def test_mixing_wells_that_do_not_fit_are_rejected() -> None:
    with pytest.raises(ValueError):
        build_ink_cap_tray(
            InkCapTrayParameters(
                width=160,
                depth=90,
                mixing_well_count=2,
            )
        )


def test_standalone_basin_is_a_plain_enclosed_box() -> None:
    """No sink assumed: the default basin must be a simple box the
    same footprint as the rack, not a spout-fed shape."""
    parameters = default_parameters()
    basin = build_ink_cap_tray(parameters)["basin"].val()
    bounds = basin.BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.width)
    assert bounds.ylen == pytest.approx(parameters.depth + parameters.label_height)
    assert bounds.zlen == pytest.approx(parameters.basin_height)


def test_standalone_basin_holds_material_on_every_side() -> None:
    """Unlike the sink-edge basin, the standalone tray has a wall on
    all four sides -- nothing drains out the front."""
    parameters = default_parameters()
    basin = build_ink_cap_tray(parameters)["basin"].val()

    mid_z = parameters.basin_height / 2
    front_y = parameters.depth / 2 - parameters.wall / 2

    assert basin.isInside(cq.Vector(0, front_y, mid_z))


def test_liner_groove_cuts_a_localized_band_in_the_wall() -> None:
    """The groove should bite partway into the wall, in a thin Z band
    near the rim -- not puncture through to the outer face, and not
    run the full height of the wall."""
    parameters = default_parameters()
    basin = build_ink_cap_tray(parameters)["basin"].val()

    groove_z = parameters.basin_height - parameters.liner_groove_offset
    groove_wall_remaining = parameters.wall - parameters.liner_groove_depth
    cut_x = parameters.width / 2 - (parameters.wall + groove_wall_remaining) / 2
    solid_near_outer_x = parameters.width / 2 - groove_wall_remaining / 2
    away_from_groove_z = parameters.basin_height / 2

    assert not basin.isInside(cq.Vector(cut_x, 0, groove_z))
    assert basin.isInside(cq.Vector(solid_near_outer_x, 0, groove_z))
    assert basin.isInside(cq.Vector(cut_x, 0, away_from_groove_z))


def test_liner_groove_can_be_disabled() -> None:
    parameters = InkCapTrayParameters(
        width=160,
        depth=90,
        wall=3,
        basin_height=16,
        standalone_floor=3,
        liner_groove=False,
    )
    basin = build_ink_cap_tray(parameters)["basin"].val()

    groove_z = parameters.basin_height - parameters.liner_groove_offset
    would_be_cut_x = parameters.width / 2 - 2.6

    assert basin.isInside(cq.Vector(would_be_cut_x, 0, groove_z))


def test_liner_groove_deeper_than_wall_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_ink_cap_tray(
            InkCapTrayParameters(
                width=160,
                depth=90,
                wall=3,
                liner_groove_depth=3,
            )
        )


def test_sink_edge_basin_matches_drainage_basin_bounds() -> None:
    """The sink-edge basin must behave identically to the one
    drip_tray and sponge_caddy use -- same sloped floor, same flaring
    spout."""
    parameters = sink_edge_parameters()
    parts = build_ink_cap_tray(parameters)
    bounds = parts["basin"].val().BoundingBox()

    interior_width = parameters.width - 2 * parameters.wall
    tip_width = interior_width + 2 * parameters.spout_flare_margin

    assert bounds.xlen == pytest.approx(max(parameters.width, tip_width))
    assert bounds.ylen == pytest.approx(
        parameters.depth + parameters.spout_length + parameters.label_height
    )
    assert bounds.zlen == pytest.approx(parameters.basin_height)


def test_invalid_ink_cap_tray_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_ink_cap_tray(
            InkCapTrayParameters(
                width=160,
                depth=90,
                cap_count=20,
                cap_spacing=20,
            )
        )


def test_oversized_cap_hole_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_ink_cap_tray(
            InkCapTrayParameters(
                width=160,
                depth=90,
                cap_diameter=25,
                cap_spacing=20,
            )
        )


def test_invalid_basin_style_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_ink_cap_tray(
            InkCapTrayParameters(
                width=160,
                depth=90,
                basin_style="countertop",
            )
        )
