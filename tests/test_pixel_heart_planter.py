"""Tests for the pixel-art heart planter generator."""

from dataclasses import replace

import pytest

from zcad.generators.pixel_heart_planter import (
    HEART_PATTERN,
    PixelHeartPlanterParameters,
    build_pixel_heart_planter,
    build_planter,
    build_saucer,
)


def default_parameters() -> PixelHeartPlanterParameters:
    """A representative planter with labels disabled for speed."""
    return PixelHeartPlanterParameters(
        pixel_size=12,
        height_pixels=4,
        wall=2.4,
        floor=3,
        groove_depth=0.6,
        groove_width=1.0,
        drain_hole_diameter=5,
        clearance=0.5,
        lip_wall=2,
        lip_height=8,
        rib_height=1.5,
        rib_width=1.6,
        plate_thickness=3,
        plate_margin=6,
        plate_corner_radius=6,
        strip_depth=22,
        label="",
    )


def test_returns_planter_and_saucer() -> None:
    parts = build_pixel_heart_planter(default_parameters())

    assert set(parts) == {"planter", "saucer"}


def test_parts_are_single_valid_solids() -> None:
    parts = build_pixel_heart_planter(default_parameters())

    for model in parts.values():
        assert model.val().isValid()
        assert model.val().Volume() > 0
        assert len(model.solids().vals()) == 1


def test_outline_is_closed_counter_clockwise_loop() -> None:
    parameters = default_parameters()
    loop = parameters.grid.trace_outline()

    # Shoelace area in grid units: positive means counter-clockwise
    # in the XY frame where +Y points to row 0.
    points = [parameters.grid.grid_corner(corner) for corner in loop]
    area = sum(
        points[index - 1][0] * points[index][1]
        - points[index][0] * points[index - 1][1]
        for index in range(len(points))
    )

    filled_area = len(parameters.filled_pixels()) * parameters.pixel_size**2

    assert area / 2 == pytest.approx(filled_area)
    assert len(parameters.grid.outline_corners()) < len(loop)


def test_offset_outline_grows_and_shrinks_symmetrically() -> None:
    parameters = default_parameters()

    outer = parameters.grid.offset_outline(3.0)
    inner = parameters.grid.offset_outline(-3.0)

    def width(points: tuple[tuple[float, float], ...]) -> float:
        xs = [x for x, _y in points]
        return max(xs) - min(xs)

    assert width(outer) == pytest.approx(parameters.heart_width + 6.0)
    assert width(inner) == pytest.approx(parameters.heart_width - 6.0)


def test_planter_bounds_match_pattern() -> None:
    parameters = default_parameters()
    bounds = build_planter(parameters).val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.heart_width)
    assert bounds.ylen == pytest.approx(parameters.heart_depth)
    assert bounds.zlen == pytest.approx(parameters.planter_height)


def test_planter_is_hollow_with_drain_holes() -> None:
    parameters = default_parameters()
    solid_volume = (
        len(parameters.filled_pixels())
        * parameters.pixel_size**2
        * parameters.planter_height
    )

    volume = build_planter(parameters).val().Volume()

    assert 0 < volume < 0.5 * solid_volume
    assert len(parameters.drain_hole_pixels()) > 0


def test_grooves_remove_material() -> None:
    parameters = default_parameters()
    plain = replace(parameters, groove_depth=0.0)

    assert (
        build_planter(parameters).val().Volume() < build_planter(plain).val().Volume()
    )


def test_saucer_bounds_include_label_strip() -> None:
    parameters = default_parameters()
    bounds = build_saucer(parameters).val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.plate_width)
    assert bounds.ylen == pytest.approx(parameters.plate_depth)
    assert bounds.zlen == pytest.approx(parameters.saucer_height)


def test_planter_fits_inside_saucer_pocket() -> None:
    """The planter, resting on the ribs, must not intersect the saucer."""
    parameters = default_parameters()
    parts = build_pixel_heart_planter(parameters)

    seated = parts["planter"].translate(
        (0.0, 0.0, parameters.plate_thickness + parameters.rib_height)
    )
    overlap = seated.intersect(parts["saucer"])

    assert overlap.val().Volume() == pytest.approx(0.0, abs=1e-6)


def test_label_embosses_above_plate() -> None:
    labelled = replace(
        default_parameters(),
        label="P1 + P2",
        subtitle="CO-OP",
    )
    plain = default_parameters()

    labelled_volume = build_saucer(labelled).val().Volume()
    plain_volume = build_saucer(plain).val().Volume()

    assert labelled_volume > plain_volume


def test_default_pattern_is_the_heart() -> None:
    assert PixelHeartPlanterParameters().rows == HEART_PATTERN


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"wall": 1.5, "groove_depth": 0.6}, "groove_depth"),
        ({"pixel_size": 5}, "pixel_size"),
        ({"drain_hole_diameter": 8}, "drain_hole_diameter"),
        ({"rib_height": 9}, "rib_height"),
        ({"height_pixels": 0}, "height_pixels"),
        ({"pattern": ("XX", "X")}, "same length"),
        ({"pattern": ("X.", ".X")}, "corner"),
        ({"pattern": ("X.X",)}, "connected"),
    ],
)
def test_invalid_parameters_are_rejected(
    changes: dict[str, object],
    message: str,
) -> None:
    parameters = replace(default_parameters(), **changes)

    with pytest.raises(ValueError, match=message):
        build_pixel_heart_planter(parameters)
