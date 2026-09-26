"""Pixel coaster: a square coaster with a flush pixel-art relief.

The top face is recessed inside a rim, and the pixel icon rises back
out of the recess to sit flush with the rim, so a glass rests on rim
and icon together and never rocks. Pausing the print at the recess
floor and swapping filament colours the icon and the rim in one go.
The relief is a plain union of pixel boxes, so any pattern works,
including ones with separate islands like the buttons on a gamepad.
"""

from dataclasses import dataclass, field

import cadquery as cq

from zcad.generators.pixel_grid import PixelGrid

ModelParts = dict[str, cq.Workplane]

GAMEPAD_PATTERN: tuple[str, ...] = (
    ".XXXXXXXXXXXXX.",
    "XXXXXXXXXXXXXXX",
    "XX.XXXXXXXXX.XX",
    "X...XXXXX.X.X.X",
    "XX.XXXXXXXXX.XX",
    "XXXX.......XXXX",
    "XXX.........XXX",
)


@dataclass(frozen=True)
class PixelCoasterParameters:
    """Dimensions for the coaster body and its relief."""

    size: float = 92.0
    thickness: float = 5.0
    corner_radius: float = 6.0
    rim_width: float = 5.0
    recess_depth: float = 1.2

    pixel_size: float = 5.0
    pattern: tuple[str, ...] = field(default_factory=lambda: GAMEPAD_PATTERN)
    pixel_inset: float = 0.25

    @property
    def grid(self) -> PixelGrid:
        return PixelGrid(rows=tuple(self.pattern), pixel_size=self.pixel_size)

    @property
    def recess_size(self) -> float:
        return self.size - 2 * self.rim_width

    @property
    def recess_floor_z(self) -> float:
        return self.thickness - self.recess_depth

    def validate(self) -> None:
        for name, value in {
            "size": self.size,
            "thickness": self.thickness,
            "rim_width": self.rim_width,
            "recess_depth": self.recess_depth,
            "pixel_size": self.pixel_size,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        for name, value in {
            "corner_radius": self.corner_radius,
            "pixel_inset": self.pixel_inset,
        }.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

        self.grid.validate_shape()

        if self.recess_depth >= self.thickness - 1.2:
            raise ValueError("recess_depth leaves less than 1.2mm under the icon")

        if self.recess_size <= 0:
            raise ValueError("rim_width is too wide for size")

        if self.grid.width > self.recess_size or self.grid.depth > self.recess_size:
            raise ValueError("pattern does not fit inside the recess")

        if 2 * self.pixel_inset >= self.pixel_size:
            raise ValueError("pixel_inset is too large for pixel_size")


def build_coaster(
    parameters: PixelCoasterParameters,
) -> cq.Workplane:
    """Recessed square with the pixel relief raised back to flush."""
    body = cq.Workplane("XY").box(
        parameters.size,
        parameters.size,
        parameters.thickness,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        body = body.edges("|Z").fillet(parameters.corner_radius)

    recess = (
        cq.Workplane("XY")
        .workplane(offset=parameters.recess_floor_z)
        .rect(parameters.recess_size, parameters.recess_size)
        .extrude(parameters.recess_depth + 0.5)
    )

    inner_radius = max(parameters.corner_radius - parameters.rim_width, 0.0)

    if inner_radius > 0:
        recess = recess.edges("|Z").fillet(inner_radius)

    body = body.cut(recess)

    relief = parameters.grid.relief(
        height=parameters.recess_depth,
        base_z=parameters.recess_floor_z,
        inset=parameters.pixel_inset,
    )

    return body.union(relief)


def build_pixel_coaster(
    parameters: PixelCoasterParameters,
) -> ModelParts:
    """Build the single coaster."""
    parameters.validate()

    return {"main": build_coaster(parameters)}
