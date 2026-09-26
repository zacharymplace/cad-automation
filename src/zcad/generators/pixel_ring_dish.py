"""Pixel ring dish: a shallow pixel-heart tray with a cone for rings.

The dish is the planter's little sibling: the same traced outline and
scored walls, a low rim, no drainage, and a tapered cone rising from
the floor of one interior pixel so two rings can sit on it without
rolling off. It lives on a nightstand. One part, printed flat, no
supports; the cone's taper is well inside what FDM prints unaided.
"""

from dataclasses import dataclass, field

import cadquery as cq

from zcad.generators.pixel_grid import GridPoint, PixelGrid

ModelParts = dict[str, cq.Workplane]

HEART_PATTERN: tuple[str, ...] = (
    ".XX...XX.",
    "XXXX.XXXX",
    "XXXXXXXXX",
    "XXXXXXXXX",
    ".XXXXXXX.",
    "..XXXXX..",
    "...XXX...",
    "....X....",
)


@dataclass(frozen=True)
class PixelRingDishParameters:
    """Dimensions for the dish and its ring cone."""

    pixel_size: float = 10.0
    pattern: tuple[str, ...] = field(default_factory=lambda: HEART_PATTERN)
    wall: float = 2.4
    floor: float = 3.0
    rim_height: float = 12.0

    groove_depth: float = 0.5
    groove_width: float = 0.8

    cone_pixel: tuple[int, int] = (3, 4)
    cone_base_diameter: float = 18.0
    cone_top_diameter: float = 10.0
    cone_height: float = 32.0

    @property
    def grid(self) -> PixelGrid:
        return PixelGrid(rows=tuple(self.pattern), pixel_size=self.pixel_size)

    @property
    def total_height(self) -> float:
        return max(self.rim_height, self.floor + self.cone_height)

    def validate(self) -> None:
        for name, value in {
            "pixel_size": self.pixel_size,
            "wall": self.wall,
            "floor": self.floor,
            "rim_height": self.rim_height,
            "cone_base_diameter": self.cone_base_diameter,
            "cone_top_diameter": self.cone_top_diameter,
            "cone_height": self.cone_height,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        for name, value in {
            "groove_depth": self.groove_depth,
            "groove_width": self.groove_width,
        }.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

        self.grid.validate()

        if self.wall - self.groove_depth < 1.2:
            raise ValueError("groove_depth leaves less than 1.2mm of wall")

        if self.pixel_size <= 2 * self.wall + 2 * self.groove_depth:
            raise ValueError("pixel_size is too small for the wall thickness")

        if self.floor >= self.rim_height:
            raise ValueError("floor must be lower than rim_height")

        if self.cone_top_diameter > self.cone_base_diameter:
            raise ValueError("cone_top_diameter must not exceed cone_base_diameter")

        cone_pixel: GridPoint = tuple(self.cone_pixel)  # type: ignore[assignment]

        if cone_pixel not in self.grid.interior_pixels():
            raise ValueError("cone_pixel must be an interior pixel of the pattern")

        # An interior pixel has filled neighbours, so a disc of radius
        # 1.5 pixels around its centre stays inside the outline.
        reach = 1.5 * self.pixel_size - self.wall

        if self.cone_base_diameter / 2 > reach:
            raise ValueError("cone_base_diameter does not fit inside the cavity")


def build_dish(
    parameters: PixelRingDishParameters,
) -> cq.Workplane:
    """Low pixel tray with a ring cone."""
    grid = parameters.grid

    body = grid.outline_prism(offset=0.0, height=parameters.rim_height)
    cavity = grid.outline_prism(
        offset=-parameters.wall,
        height=parameters.rim_height,
        base_z=parameters.floor,
    )
    body = body.cut(cavity)

    body = grid.score_walls(
        body,
        height=parameters.rim_height,
        depth=parameters.groove_depth,
        width=parameters.groove_width,
        levels=1,
    )

    x, y = grid.pixel_center(tuple(parameters.cone_pixel))  # type: ignore[arg-type]
    overlap = 0.5
    cone = cq.Solid.makeCone(
        parameters.cone_base_diameter / 2,
        parameters.cone_top_diameter / 2,
        parameters.cone_height + overlap,
        cq.Vector(x, y, parameters.floor - overlap),
        cq.Vector(0, 0, 1),
    )

    return body.union(cq.Workplane("XY").newObject([cone]))


def build_pixel_ring_dish(
    parameters: PixelRingDishParameters,
) -> ModelParts:
    """Build the single dish."""
    parameters.validate()

    return {"main": build_dish(parameters)}
