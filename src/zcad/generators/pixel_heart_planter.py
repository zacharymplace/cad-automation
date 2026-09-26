"""Pixel-art heart planter with an "achievement banner" drip plate.

Two parts. The `planter` is a hollow pixel heart -- every outline
step is one `pixel_size` square -- with shallow grooves scored into
the outer walls at each pixel boundary so the blocks read from across
a room, and drainage holes through the floor. The `saucer` is a
rounded plate with a raised pixel-outline lip that the planter drops
into, drainage ribs across the pocket floor so the planter never sits
in its own runoff, and an embossed label strip along the front.

The heart pattern is a small grid of strings and can be replaced
with any other pixel shape the shared `PixelGrid` can trace: a single
connected region without holes whose pixels touch on full edges.
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
class PixelHeartPlanterParameters:
    """Dimensions for the pixel planter and its banner saucer."""

    pixel_size: float = 12.0
    height_pixels: int = 4
    wall: float = 2.4
    floor: float = 3.0
    pattern: tuple[str, ...] = field(default_factory=lambda: HEART_PATTERN)

    groove_depth: float = 0.6
    groove_width: float = 1.0
    drain_hole_diameter: float = 5.0

    clearance: float = 0.5
    lip_wall: float = 2.0
    lip_height: float = 8.0
    rib_height: float = 1.5
    rib_width: float = 1.6

    plate_thickness: float = 3.0
    plate_margin: float = 6.0
    plate_corner_radius: float = 6.0
    strip_depth: float = 22.0

    label: str = "PLAYER 2 HAS JOINED"
    label_size: float = 6.5
    label_height: float = 0.8
    subtitle: str = ""
    subtitle_size: float = 4.0

    @property
    def grid(self) -> PixelGrid:
        return PixelGrid(rows=tuple(self.pattern), pixel_size=self.pixel_size)

    @property
    def rows(self) -> tuple[str, ...]:
        return tuple(self.pattern)

    @property
    def heart_width(self) -> float:
        return self.grid.width

    @property
    def heart_depth(self) -> float:
        return self.grid.depth

    @property
    def planter_height(self) -> float:
        return self.height_pixels * self.pixel_size

    @property
    def pocket_offset(self) -> float:
        return self.clearance

    @property
    def lip_offset(self) -> float:
        return self.clearance + self.lip_wall

    @property
    def plate_width(self) -> float:
        return self.heart_width + 2 * self.lip_offset + 2 * self.plate_margin

    @property
    def plate_depth(self) -> float:
        return (
            self.heart_depth
            + 2 * self.lip_offset
            + 2 * self.plate_margin
            + self.strip_depth
        )

    @property
    def plate_center_y(self) -> float:
        """The heart is centered on the origin; the label strip hangs
        below it (-Y), so the plate's centroid shifts forward."""
        return -self.strip_depth / 2

    @property
    def strip_center_y(self) -> float:
        return -self.heart_depth / 2 - self.lip_offset - self.strip_depth / 2

    @property
    def saucer_height(self) -> float:
        return self.plate_thickness + self.lip_height

    def filled_pixels(self) -> frozenset[GridPoint]:
        return self.grid.filled_pixels()

    def drain_hole_pixels(self) -> tuple[GridPoint, ...]:
        """Every other interior pixel, checkerboard style."""
        return tuple(
            (row, column)
            for row, column in self.grid.interior_pixels()
            if (row + column) % 2 == 0
        )

    def validate(self) -> None:
        positive_values = {
            "pixel_size": self.pixel_size,
            "wall": self.wall,
            "floor": self.floor,
            "lip_wall": self.lip_wall,
            "lip_height": self.lip_height,
            "plate_thickness": self.plate_thickness,
            "label_size": self.label_size,
            "label_height": self.label_height,
            "subtitle_size": self.subtitle_size,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        for name, value in {
            "groove_depth": self.groove_depth,
            "groove_width": self.groove_width,
            "drain_hole_diameter": self.drain_hole_diameter,
            "clearance": self.clearance,
            "rib_height": self.rib_height,
            "rib_width": self.rib_width,
            "plate_margin": self.plate_margin,
            "plate_corner_radius": self.plate_corner_radius,
            "strip_depth": self.strip_depth,
        }.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

        if self.height_pixels < 1:
            raise ValueError("height_pixels must be at least 1")

        self.grid.validate()

        if self.wall - self.groove_depth < 1.2:
            raise ValueError("groove_depth leaves less than 1.2mm of wall")

        if self.pixel_size <= 2 * self.wall + 2 * self.groove_depth:
            raise ValueError("pixel_size is too small for the wall thickness")

        if self.pixel_size <= 2 * self.lip_offset:
            raise ValueError("pixel_size is too small for the saucer lip")

        if self.drain_hole_diameter >= self.pixel_size - 2 * self.wall:
            raise ValueError("drain_hole_diameter does not fit inside one pixel")

        if self.floor >= self.planter_height:
            raise ValueError("floor must be thinner than the planter height")

        if self.rib_height >= self.lip_height:
            raise ValueError("rib_height must be lower than lip_height")

        if self.label and self.strip_depth < self.label_size:
            raise ValueError("strip_depth is too shallow for the label")


def build_planter(
    parameters: PixelHeartPlanterParameters,
) -> cq.Workplane:
    """Hollow pixel heart with scored walls and floor drainage."""
    grid = parameters.grid

    body = grid.outline_prism(offset=0.0, height=parameters.planter_height)
    cavity = grid.outline_prism(
        offset=-parameters.wall,
        height=parameters.planter_height,
        base_z=parameters.floor,
    )
    body = body.cut(cavity)

    if parameters.drain_hole_diameter > 0:
        margin = 0.5

        for pixel in parameters.drain_hole_pixels():
            x, y = grid.pixel_center(pixel)
            hole = (
                cq.Workplane("XY")
                .workplane(offset=-margin)
                .center(x, y)
                .circle(parameters.drain_hole_diameter / 2)
                .extrude(parameters.floor + 2 * margin)
            )
            body = body.cut(hole)

    return grid.score_walls(
        body,
        height=parameters.planter_height,
        depth=parameters.groove_depth,
        width=parameters.groove_width,
        levels=parameters.height_pixels,
    )


def _emboss_label(
    plate: cq.Workplane,
    parameters: PixelHeartPlanterParameters,
) -> cq.Workplane:
    """Raise the label (and subtitle) on the front strip."""
    lines: list[tuple[str, float]] = []

    if parameters.label:
        lines.append((parameters.label, parameters.label_size))

    if parameters.subtitle:
        lines.append((parameters.subtitle, parameters.subtitle_size))

    if not lines:
        return plate

    gap = 0.6 * min(size for _text, size in lines)
    total = sum(size for _text, size in lines) + gap * (len(lines) - 1)
    cursor = parameters.strip_center_y + total / 2
    usable_width = parameters.plate_width - 2 * parameters.plate_margin

    for text, size in lines:
        center_y = cursor - size / 2
        cursor -= size + gap

        letters = (
            cq.Workplane("XY")
            .workplane(offset=parameters.plate_thickness)
            .center(0, center_y)
            .text(
                text,
                size,
                parameters.label_height,
                kind="bold",
                halign="center",
                valign="center",
            )
        )

        bounds = letters.val().BoundingBox()

        if bounds.xlen > usable_width:
            raise ValueError(
                f"label {text!r} is {bounds.xlen:.1f}mm wide; "
                f"only {usable_width:.1f}mm is available on the plate"
            )

        plate = plate.union(letters)

    return plate


def build_saucer(
    parameters: PixelHeartPlanterParameters,
) -> cq.Workplane:
    """Rounded plate with a pixel-outline lip, drainage ribs, and label."""
    grid = parameters.grid

    plate = (
        cq.Workplane("XY")
        .box(
            parameters.plate_width,
            parameters.plate_depth,
            parameters.plate_thickness,
            centered=(True, True, False),
        )
        .translate((0.0, parameters.plate_center_y, 0.0))
    )

    if parameters.plate_corner_radius > 0:
        plate = plate.edges("|Z").fillet(parameters.plate_corner_radius)

    lip = grid.outline_prism(
        offset=parameters.lip_offset,
        height=parameters.lip_height,
        base_z=parameters.plate_thickness,
    ).cut(
        grid.outline_prism(
            offset=parameters.pocket_offset,
            height=parameters.lip_height,
            base_z=parameters.plate_thickness,
        )
    )
    plate = plate.union(lip)

    if parameters.rib_height > 0 and parameters.rib_width > 0:
        pocket = grid.outline_prism(
            offset=parameters.pocket_offset,
            height=parameters.rib_height,
            base_z=parameters.plate_thickness,
        )
        ribs = None

        for row in range(1, grid.row_count):
            _x, y = grid.grid_corner((row, 0))
            rib = (
                cq.Workplane("XY")
                .workplane(offset=parameters.plate_thickness)
                .box(
                    parameters.heart_width + 2 * parameters.pocket_offset,
                    parameters.rib_width,
                    parameters.rib_height,
                    centered=(True, True, False),
                )
                .translate((0.0, y, 0.0))
            )
            ribs = rib if ribs is None else ribs.union(rib)

        if ribs is not None:
            plate = plate.union(ribs.intersect(pocket))

    return _emboss_label(plate, parameters)


def build_pixel_heart_planter(
    parameters: PixelHeartPlanterParameters,
) -> ModelParts:
    """Build the planter and its saucer."""
    parameters.validate()

    return {
        "planter": build_planter(parameters),
        "saucer": build_saucer(parameters),
    }
