"""Pixel-art geometry shared by the pixel product line.

A pattern is a grid of strings, `X` for a filled pixel and `.` for
empty, row 0 at the top (+Y). `PixelGrid` centres the pattern on the
origin and offers the pieces every pixel product needs: pixel centres
and corners, a traced outline with sharp corners, an exact rectilinear
offset of that outline (positive grows outward), prisms from either,
and groove scoring along pixel boundaries on a prism's outer walls.

The outline tracer requires a single connected region without holes
whose pixels touch on full edges only; `validate` enforces that.
Products that only need a relief (a union of pixel boxes) can skip the
outline and accept any pattern.
"""

from dataclasses import dataclass

import cadquery as cq

GridPoint = tuple[int, int]
Point = tuple[float, float]

FILLED = "X"


@dataclass(frozen=True)
class PixelGrid:
    """A pixel pattern placed on a square grid of `pixel_size` mm."""

    rows: tuple[str, ...]
    pixel_size: float

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.rows[0]) if self.rows else 0

    @property
    def width(self) -> float:
        return self.column_count * self.pixel_size

    @property
    def depth(self) -> float:
        return self.row_count * self.pixel_size

    def filled_pixels(self) -> frozenset[GridPoint]:
        """`(row, column)` of every filled pixel."""
        return frozenset(
            (row_index, column_index)
            for row_index, row in enumerate(self.rows)
            for column_index, cell in enumerate(row)
            if cell == FILLED
        )

    def interior_pixels(self) -> tuple[GridPoint, ...]:
        """Filled pixels whose four edge-neighbours are also filled."""
        filled = self.filled_pixels()

        return tuple(
            sorted(
                (row, column)
                for row, column in filled
                if {
                    (row - 1, column),
                    (row + 1, column),
                    (row, column - 1),
                    (row, column + 1),
                }
                <= filled
            )
        )

    def pixel_center(self, pixel: GridPoint) -> Point:
        row, column = pixel
        return (
            (column - self.column_count / 2) * self.pixel_size + self.pixel_size / 2,
            (self.row_count / 2 - row) * self.pixel_size - self.pixel_size / 2,
        )

    def grid_corner(self, corner: GridPoint) -> Point:
        """XY of a grid corner; corner `(r, c)` is the top-left of pixel
        `(r, c)`."""
        row, column = corner
        return (
            (column - self.column_count / 2) * self.pixel_size,
            (self.row_count / 2 - row) * self.pixel_size,
        )

    def validate_shape(self) -> None:
        """Basic checks any pixel product needs."""
        if self.pixel_size <= 0:
            raise ValueError("pixel_size must be greater than zero")

        if not self.rows:
            raise ValueError("pattern must contain at least one row")

        if any(len(row) != self.column_count for row in self.rows):
            raise ValueError("pattern rows must all be the same length")

        if not self.filled_pixels():
            raise ValueError("pattern must contain at least one filled pixel")

    def validate(self) -> None:
        """Checks needed before the outline can be traced or offset."""
        self.validate_shape()
        _validate_no_diagonal_contacts(self.filled_pixels())
        self.trace_outline()

    def trace_outline(self) -> tuple[GridPoint, ...]:
        """Grid corners around the filled region, counter-clockwise,
        with collinear points kept so every pixel boundary is a
        vertex."""
        edges: dict[tuple[GridPoint, GridPoint], None] = {}

        for row, column in self.filled_pixels():
            bottom_left = (row + 1, column)
            bottom_right = (row + 1, column + 1)
            top_right = (row, column + 1)
            top_left = (row, column)

            for start, end in (
                (bottom_left, bottom_right),
                (bottom_right, top_right),
                (top_right, top_left),
                (top_left, bottom_left),
            ):
                if (end, start) in edges:
                    del edges[(end, start)]
                else:
                    edges[(start, end)] = None

        next_corner = {start: end for start, end in edges}

        if len(next_corner) != len(edges):
            raise ValueError("pattern outline branches; pixels may only touch on edges")

        start = min(next_corner)
        loop = [start]
        current = start

        while True:
            current = next_corner[current]

            if current == start:
                break

            loop.append(current)

        if len(loop) != len(next_corner):
            # Leftover boundary edges belong to a second loop: either a
            # separate island or a hole inside the region.
            raise ValueError("pattern must be a single connected region without holes")

        return tuple(loop)

    def outline_corners(self) -> tuple[GridPoint, ...]:
        """The outline with collinear points dropped."""
        loop = self.trace_outline()
        count = len(loop)

        return tuple(
            loop[index]
            for index in range(count)
            if is_corner(loop[index - 1], loop[index], loop[(index + 1) % count])
        )

    def offset_outline(self, distance: float) -> tuple[Point, ...]:
        """Offset the outline by `distance` (positive grows outward)
        keeping every corner sharp. Exact while no edge is shorter
        than twice the inward offset."""
        points = [self.grid_corner(corner) for corner in self.outline_corners()]
        count = len(points)
        result = []

        for index in range(count):
            previous = points[index - 1]
            point = points[index]
            following = points[(index + 1) % count]

            incoming = _unit(previous, point)
            outgoing = _unit(point, following)

            # The outline runs counter-clockwise, so the outward normal
            # of each edge is its direction rotated clockwise.
            normal_in = (incoming[1], -incoming[0])
            normal_out = (outgoing[1], -outgoing[0])

            result.append(
                (
                    point[0] + distance * (normal_in[0] + normal_out[0]),
                    point[1] + distance * (normal_in[1] + normal_out[1]),
                )
            )

        return tuple(result)

    def outline_prism(
        self,
        *,
        offset: float,
        height: float,
        base_z: float = 0.0,
    ) -> cq.Workplane:
        """Extrude the (offset) outline."""
        return prism(self.offset_outline(offset), height=height, base_z=base_z)

    def relief(
        self,
        *,
        height: float,
        base_z: float = 0.0,
        inset: float = 0.0,
    ) -> cq.Workplane:
        """Union of one box per filled pixel; works for any pattern,
        including disconnected ones. `inset` shrinks each box so
        neighbouring pixels read as separate tiles."""
        size = self.pixel_size - 2 * inset

        if size <= 0:
            raise ValueError("inset is too large for pixel_size")

        result: cq.Workplane | None = None

        for pixel in sorted(self.filled_pixels()):
            x, y = self.pixel_center(pixel)
            box = (
                cq.Workplane("XY")
                .box(size, size, height, centered=(True, True, False))
                .translate((x, y, base_z))
            )
            result = box if result is None else result.union(box)

        if result is None:
            raise ValueError("pattern must contain at least one filled pixel")

        return result

    def score_face(
        self,
        body: cq.Workplane,
        *,
        z: float,
        depth: float,
        width: float,
    ) -> cq.Workplane:
        """Score the flat face at height `z` along every grid line that
        two filled pixels share, so a flat pixel shape reads as tiles.
        Pairs with `score_walls`, whose vertical grooves meet these at
        the outline."""
        if depth <= 0 or width <= 0:
            return body

        filled = self.filled_pixels()
        half = self.pixel_size / 2

        for row, column in sorted(filled):
            x, y = self.pixel_center((row, column))

            if (row, column + 1) in filled:
                groove = cq.Workplane("XY").box(width, self.pixel_size, 2 * depth)
                body = body.cut(groove.translate((x + half, y, z)))

            if (row + 1, column) in filled:
                groove = cq.Workplane("XY").box(self.pixel_size, width, 2 * depth)
                body = body.cut(groove.translate((x, y - half, z)))

        return body

    def score_walls(
        self,
        body: cq.Workplane,
        *,
        height: float,
        depth: float,
        width: float,
        levels: int,
    ) -> cq.Workplane:
        """Score the outer walls of an outline prism along every pixel
        boundary: a ring at each of `levels` pixel heights and a
        vertical line at each mid-edge grid point."""
        if depth <= 0 or width <= 0:
            return body

        for level in range(1, levels):
            z = level * self.pixel_size - width / 2
            ring = self.outline_prism(offset=0.0, height=width, base_z=z).cut(
                self.outline_prism(offset=-depth, height=width, base_z=z)
            )
            body = body.cut(ring)

        loop = self.trace_outline()
        count = len(loop)
        margin = 0.5

        for index in range(count):
            previous = loop[index - 1]
            point = loop[index]
            following = loop[(index + 1) % count]

            if is_corner(previous, point, following):
                continue

            x, y = self.grid_corner(point)
            runs_along_x = following[1] != point[1]

            groove = cq.Workplane("XY").box(
                width if runs_along_x else 2 * depth,
                2 * depth if runs_along_x else width,
                height + 2 * margin,
                centered=(True, True, False),
            )
            body = body.cut(groove.translate((x, y, -margin)))

        return body


def is_corner(previous: GridPoint, point: GridPoint, following: GridPoint) -> bool:
    incoming = (point[0] - previous[0], point[1] - previous[1])
    outgoing = (following[0] - point[0], following[1] - point[1])
    return incoming != outgoing


def prism(
    points: tuple[Point, ...],
    *,
    height: float,
    base_z: float = 0.0,
) -> cq.Workplane:
    """Extrude a closed polygon upward from `base_z`."""
    return (
        cq.Workplane("XY")
        .workplane(offset=base_z)
        .polyline(list(points))
        .close()
        .extrude(height)
    )


def _unit(start: Point, end: Point) -> Point:
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    length = (delta_x**2 + delta_y**2) ** 0.5
    return (delta_x / length, delta_y / length)


def _validate_no_diagonal_contacts(filled: frozenset[GridPoint]) -> None:
    """Pixels touching only at a corner give an ambiguous outline."""
    for row, column in filled:
        for row_step, column_step in ((1, 1), (1, -1)):
            diagonal = (row + row_step, column + column_step)

            if diagonal not in filled:
                continue

            if (row + row_step, column) in filled:
                continue

            if (row, column + column_step) in filled:
                continue

            raise ValueError(
                f"pattern pixels {(row, column)} and {diagonal} touch only at a corner"
            )
