"""Tests for the shared pixel-art geometry."""

import pytest

from zcad.generators.pixel_grid import PixelGrid

HEART = (
    ".XX...XX.",
    "XXXX.XXXX",
    "XXXXXXXXX",
    "XXXXXXXXX",
    ".XXXXXXX.",
    "..XXXXX..",
    "...XXX...",
    "....X....",
)


def heart() -> PixelGrid:
    return PixelGrid(rows=HEART, pixel_size=10.0)


def polygon_area(points: tuple[tuple[float, float], ...]) -> float:
    return (
        sum(
            points[index - 1][0] * points[index][1]
            - points[index][0] * points[index - 1][1]
            for index in range(len(points))
        )
        / 2
    )


def test_grid_is_centered_on_the_origin() -> None:
    grid = heart()

    assert grid.width == pytest.approx(90.0)
    assert grid.depth == pytest.approx(80.0)
    assert grid.grid_corner((0, 0)) == pytest.approx((-45.0, 40.0))
    assert grid.pixel_center((7, 4)) == pytest.approx((0.0, -35.0))


def test_outline_encloses_exactly_the_filled_area() -> None:
    grid = heart()
    loop = tuple(grid.grid_corner(corner) for corner in grid.trace_outline())

    filled_area = len(grid.filled_pixels()) * grid.pixel_size**2

    # Positive area: the loop runs counter-clockwise.
    assert polygon_area(loop) == pytest.approx(filled_area)


def test_offset_outline_area_matches_exact_rectilinear_offset() -> None:
    """For a rectilinear polygon offset outward by d with sharp
    corners, area grows by perimeter * d plus 4 d^2 (one square per
    net convex corner)."""
    grid = heart()
    corners = grid.outline_corners()
    loop = tuple(grid.grid_corner(corner) for corner in grid.trace_outline())
    perimeter = len(loop) * grid.pixel_size
    base_area = polygon_area(loop)

    for distance in (2.0, -2.0):
        offset = grid.offset_outline(distance)
        expected = base_area + perimeter * distance + 4 * distance**2

        assert len(offset) == len(corners)
        assert polygon_area(offset) == pytest.approx(expected)


def test_interior_pixels_have_four_filled_neighbours() -> None:
    grid = heart()
    interior = grid.interior_pixels()

    assert (3, 4) in interior
    assert (0, 1) not in interior
    assert (7, 4) not in interior


def test_relief_accepts_islands() -> None:
    grid = PixelGrid(rows=("X.X", "...", "X.X"), pixel_size=4.0)
    relief = grid.relief(height=2.0, inset=0.5)

    assert relief.val().isValid()
    assert relief.val().Volume() == pytest.approx(4 * 3.0 * 3.0 * 2.0)


def test_outline_prism_volume() -> None:
    grid = heart()
    prism = grid.outline_prism(offset=0.0, height=5.0)

    assert prism.val().Volume() == pytest.approx(len(grid.filled_pixels()) * 100 * 5)


def test_score_face_and_walls_remove_material() -> None:
    grid = heart()
    plain = grid.outline_prism(offset=0.0, height=20.0)

    faced = grid.score_face(plain, z=20.0, depth=0.5, width=1.0)
    walled = grid.score_walls(plain, height=20.0, depth=0.5, width=1.0, levels=2)

    assert faced.val().Volume() < plain.val().Volume()
    assert walled.val().Volume() < plain.val().Volume()


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (("X.", ".X"), "corner"),
        (("X.X",), "connected"),
        (("XXX", "X.X", "XXX"), "holes"),
        (("XX", "X"), "same length"),
        (("..",), "filled pixel"),
        ((), "at least one row"),
    ],
)
def test_invalid_patterns_are_rejected(rows: tuple[str, ...], message: str) -> None:
    grid = PixelGrid(rows=rows, pixel_size=5.0)

    with pytest.raises(ValueError, match=message):
        grid.validate()
