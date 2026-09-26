"""Pixel block planter: a voxel-game style cube with a face on the front.

A hollow cube, `face_pixels` pixels on a side, with a drainage hole
and a pixel pattern recessed into the front wall. The recess is cut
one tile per filled pixel, each slightly inset so the tiles read as
separate blocks. An optional second pattern is recessed into the
left, right, and back walls so the block reads from every side.
Patterns are reliefs, not outlines, so eyes and mouths that float
free of each other are fine.

Printed cup-up with no supports. The recesses are on vertical walls,
which FDM handles cleanly, and a filament swap does nothing here; if
he wants the face darker, a marker or a dab of paint in the recess
is the trick.
"""

from dataclasses import dataclass, field

import cadquery as cq

from zcad.generators.pixel_grid import PixelGrid

ModelParts = dict[str, cq.Workplane]

CREEPER_FACE: tuple[str, ...] = (
    "........",
    "........",
    ".XX..XX.",
    ".XX..XX.",
    "...XX...",
    "..XXXX..",
    "..XXXX..",
    "..X..X..",
)

# Face frames: viewer-left-to-right axis and sign, and the outward
# normal axis and sign, so a pattern reads upright and unmirrored
# from outside on every wall.
FACES: dict[str, tuple[str, float, str, float]] = {
    "front": ("x", 1.0, "y", -1.0),
    "right": ("y", 1.0, "x", 1.0),
    "back": ("x", -1.0, "y", 1.0),
    "left": ("y", -1.0, "x", -1.0),
}


@dataclass(frozen=True)
class PixelBlockPlanterParameters:
    """Dimensions for the cube and its face reliefs."""

    pixel_size: float = 10.0
    face_pixels: int = 8
    wall: float = 2.4
    floor: float = 3.0

    front_pattern: tuple[str, ...] = field(default_factory=lambda: CREEPER_FACE)
    side_pattern: tuple[str, ...] = ()
    relief_depth: float = 1.0
    pixel_inset: float = 0.2

    drain_hole_diameter: float = 6.0

    @property
    def size(self) -> float:
        return self.face_pixels * self.pixel_size

    @property
    def front_grid(self) -> PixelGrid:
        return PixelGrid(rows=tuple(self.front_pattern), pixel_size=self.pixel_size)

    @property
    def side_grid(self) -> PixelGrid | None:
        if not self.side_pattern:
            return None
        return PixelGrid(rows=tuple(self.side_pattern), pixel_size=self.pixel_size)

    def validate(self) -> None:
        for name, value in {
            "pixel_size": self.pixel_size,
            "wall": self.wall,
            "floor": self.floor,
            "relief_depth": self.relief_depth,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        for name, value in {
            "pixel_inset": self.pixel_inset,
            "drain_hole_diameter": self.drain_hole_diameter,
        }.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

        if self.face_pixels < 2:
            raise ValueError("face_pixels must be at least 2")

        if self.wall - self.relief_depth < 1.2:
            raise ValueError("relief_depth leaves less than 1.2mm of wall")

        if 2 * self.pixel_inset >= self.pixel_size:
            raise ValueError("pixel_inset is too large for pixel_size")

        if self.size - 2 * self.wall <= self.drain_hole_diameter:
            raise ValueError("drain_hole_diameter does not fit inside the cavity")

        if self.floor >= self.size:
            raise ValueError("floor must be thinner than the block")

        for name, grid in (
            ("front_pattern", self.front_grid),
            ("side_pattern", self.side_grid),
        ):
            if grid is None:
                continue

            grid.validate_shape()

            if grid.width > self.size or grid.depth > self.size:
                raise ValueError(
                    f"{name} does not fit on a {self.face_pixels}-pixel face"
                )


def _face_relief(
    parameters: PixelBlockPlanterParameters,
    grid: PixelGrid,
    face: str,
) -> cq.Workplane | None:
    """Recess tiles for one wall, built directly in place."""
    along_axis, along_sign, normal_axis, normal_sign = FACES[face]
    half = parameters.size / 2
    tile = parameters.pixel_size - 2 * parameters.pixel_inset
    margin = 0.5
    depth = parameters.relief_depth + margin

    # Tile centre sits `margin` outside the wall so the cut breaks the surface.
    normal_position = normal_sign * (half - parameters.relief_depth + depth / 2)

    result: cq.Workplane | None = None

    for pixel in sorted(grid.filled_pixels()):
        u, v = grid.pixel_center(pixel)
        along_position = along_sign * u
        z = half + v

        position = {along_axis: along_position, normal_axis: normal_position}
        extent = {along_axis: tile, normal_axis: depth}

        box = cq.Workplane("XY").box(extent["x"], extent["y"], tile)
        box = box.translate((position["x"], position["y"], z))
        result = box if result is None else result.union(box)

    return result


def build_block(
    parameters: PixelBlockPlanterParameters,
) -> cq.Workplane:
    """Hollow cube with drainage and recessed face patterns."""
    size = parameters.size

    body = cq.Workplane("XY").box(size, size, size, centered=(True, True, False))

    cavity = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor)
        .rect(size - 2 * parameters.wall, size - 2 * parameters.wall)
        .extrude(size)
    )
    body = body.cut(cavity)

    if parameters.drain_hole_diameter > 0:
        margin = 0.5
        hole = (
            cq.Workplane("XY")
            .workplane(offset=-margin)
            .circle(parameters.drain_hole_diameter / 2)
            .extrude(parameters.floor + 2 * margin)
        )
        body = body.cut(hole)

    front = _face_relief(parameters, parameters.front_grid, "front")

    if front is not None:
        body = body.cut(front)

    side_grid = parameters.side_grid

    if side_grid is not None:
        for face in ("right", "back", "left"):
            relief = _face_relief(parameters, side_grid, face)

            if relief is not None:
                body = body.cut(relief)

    return body


def build_pixel_block_planter(
    parameters: PixelBlockPlanterParameters,
) -> ModelParts:
    """Build the single block."""
    parameters.validate()

    return {"main": build_block(parameters)}
