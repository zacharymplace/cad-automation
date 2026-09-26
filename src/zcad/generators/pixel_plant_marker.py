"""Pixel plant marker: a garden stake with a pixel-art head.

One flat part printed on its back. From the top down: a pixel icon
(a sprout by default) traced from a pattern, a label band with the
crop name embossed on it, and a tapered stake that pushes into soil.
The icon and the band are one prism so nothing snaps off; the icon
carries the same pixel scoring as the planter line, one groove per
pixel boundary on both its outline and its top face, so the sprout
reads as tiles and the family reads as a set.
"""

from dataclasses import dataclass, field

import cadquery as cq

from zcad.generators.pixel_grid import PixelGrid, prism

ModelParts = dict[str, cq.Workplane]

SPROUT_PATTERN: tuple[str, ...] = (
    ".XX.XX.",
    "XXX.XXX",
    ".XXXXX.",
    "..XXX..",
    "...X...",
    "...X...",
)


@dataclass(frozen=True)
class PixelPlantMarkerParameters:
    """Dimensions for the icon head, label band, and stake."""

    pixel_size: float = 5.0
    pattern: tuple[str, ...] = field(default_factory=lambda: SPROUT_PATTERN)
    thickness: float = 3.0

    groove_depth: float = 0.5
    groove_width: float = 0.8

    band_width: float = 44.0
    band_height: float = 14.0
    band_corner_radius: float = 2.0

    label: str = "TOMATO"
    label_size: float = 6.0
    label_height: float = 0.6

    stake_length: float = 110.0
    stake_top_width: float = 16.0
    stake_tip_width: float = 3.0

    @property
    def grid(self) -> PixelGrid:
        return PixelGrid(rows=tuple(self.pattern), pixel_size=self.pixel_size)

    @property
    def icon_center_y(self) -> float:
        """The band is centred on the origin; the icon sits above it."""
        return self.band_height / 2 + self.grid.depth / 2

    @property
    def stake_top_y(self) -> float:
        return -self.band_height / 2

    @property
    def total_height(self) -> float:
        return self.grid.depth + self.band_height + self.stake_length

    @property
    def total_width(self) -> float:
        return max(self.grid.width, self.band_width, self.stake_top_width)

    def validate(self) -> None:
        for name, value in {
            "pixel_size": self.pixel_size,
            "thickness": self.thickness,
            "band_width": self.band_width,
            "band_height": self.band_height,
            "label_size": self.label_size,
            "label_height": self.label_height,
            "stake_length": self.stake_length,
            "stake_top_width": self.stake_top_width,
            "stake_tip_width": self.stake_tip_width,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        for name, value in {
            "groove_depth": self.groove_depth,
            "groove_width": self.groove_width,
            "band_corner_radius": self.band_corner_radius,
        }.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

        self.grid.validate()

        if self.groove_depth >= self.pixel_size / 2:
            raise ValueError("groove_depth is too deep for pixel_size")

        if self.thickness - self.groove_depth < 1.2:
            raise ValueError("groove_depth leaves less than 1.2mm under the icon face")

        if self.stake_tip_width >= self.stake_top_width:
            raise ValueError("stake_tip_width must be narrower than stake_top_width")

        if self.stake_top_width > self.band_width:
            raise ValueError("stake_top_width must not exceed band_width")

        if self.label and self.label_size >= self.band_height:
            raise ValueError("band_height is too small for the label")

        # The icon must land on the band so the part is one piece.
        bottom_row = self.grid.row_count - 1
        bottom_pixels = [
            column for row, column in self.grid.filled_pixels() if row == bottom_row
        ]

        if not bottom_pixels:
            raise ValueError("pattern must reach its bottom row to join the band")

        for column in bottom_pixels:
            x, _y = self.grid.pixel_center((bottom_row, column))

            if abs(x) + self.pixel_size / 2 > self.band_width / 2:
                raise ValueError("pattern is wider than band_width where it joins")


def build_marker(
    parameters: PixelPlantMarkerParameters,
) -> cq.Workplane:
    """Icon, band, and stake as one flat prism with an embossed label."""
    grid = parameters.grid

    icon = grid.outline_prism(offset=0.0, height=parameters.thickness)
    icon = grid.score_walls(
        icon,
        height=parameters.thickness,
        depth=parameters.groove_depth,
        width=parameters.groove_width,
        levels=1,
    )
    icon = grid.score_face(
        icon,
        z=parameters.thickness,
        depth=parameters.groove_depth,
        width=parameters.groove_width,
    ).translate((0.0, parameters.icon_center_y, 0.0))

    band = cq.Workplane("XY").box(
        parameters.band_width,
        parameters.band_height,
        parameters.thickness,
        centered=(True, True, False),
    )

    if parameters.band_corner_radius > 0:
        band = band.edges("|Z").fillet(parameters.band_corner_radius)

    top = parameters.stake_top_y + 0.5  # overlap into the band for a clean union
    tip = parameters.stake_top_y - parameters.stake_length
    stake = prism(
        (
            (-parameters.stake_top_width / 2, top),
            (parameters.stake_top_width / 2, top),
            (parameters.stake_tip_width / 2, tip),
            (-parameters.stake_tip_width / 2, tip),
        ),
        height=parameters.thickness,
    )

    body = band.union(icon).union(stake)

    if parameters.label:
        letters = (
            cq.Workplane("XY")
            .workplane(offset=parameters.thickness)
            .text(
                parameters.label,
                parameters.label_size,
                parameters.label_height,
                kind="bold",
                halign="center",
                valign="center",
            )
        )
        bounds = letters.val().BoundingBox()

        if bounds.xlen > parameters.band_width - 4.0:
            raise ValueError(
                f"label {parameters.label!r} is {bounds.xlen:.1f}mm wide; "
                f"band_width {parameters.band_width}mm leaves too little margin"
            )

        body = body.union(letters)

    return body


def build_pixel_plant_marker(
    parameters: PixelPlantMarkerParameters,
) -> ModelParts:
    """Build the single flat marker."""
    parameters.validate()

    return {"main": build_marker(parameters)}
