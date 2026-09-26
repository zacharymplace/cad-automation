"""Pixel photo stand: a low pixel-heart block with a slanted photo slot.

The traced outline is extruded into a short solid block with scored
walls, and a slot is cut across it, leaning back a few degrees, so a
4x6 photo, a card, or a postcard stands up and rests against the
slot's back wall. The block is solid below the slot, which is what
keeps a wide photo from tipping it. One part, printed flat, no
supports; the slot is open at the top so the lean prints as a plain
angled wall.
"""

import math
from dataclasses import dataclass, field

import cadquery as cq

from zcad.generators.pixel_grid import PixelGrid

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
class PixelPhotoStandParameters:
    """Dimensions for the block and its slot."""

    pixel_size: float = 10.0
    pattern: tuple[str, ...] = field(default_factory=lambda: HEART_PATTERN)
    height: float = 14.0

    groove_depth: float = 0.5
    groove_width: float = 0.8

    slot_width: float = 2.6
    slot_depth: float = 9.0
    slot_tilt_degrees: float = 12.0
    slot_offset_y: float = 5.0

    @property
    def grid(self) -> PixelGrid:
        return PixelGrid(rows=tuple(self.pattern), pixel_size=self.pixel_size)

    def validate(self) -> None:
        for name, value in {
            "pixel_size": self.pixel_size,
            "height": self.height,
            "slot_width": self.slot_width,
            "slot_depth": self.slot_depth,
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

        if self.groove_depth >= self.pixel_size / 2:
            raise ValueError("groove_depth is too deep for pixel_size")

        if self.height - self.slot_depth < 3.0:
            raise ValueError("slot_depth leaves less than 3mm of base under the slot")

        if not 0 <= self.slot_tilt_degrees <= 30:
            raise ValueError("slot_tilt_degrees must be between 0 and 30")

        # The tilted slot drifts backward by depth * tan(tilt); keep the
        # whole slot inside the middle band of the outline.
        drift = self.slot_depth * math.tan(math.radians(self.slot_tilt_degrees))
        half_depth = self.grid.depth / 2

        if (
            abs(self.slot_offset_y) + drift + self.slot_width
            > half_depth - self.pixel_size
        ):
            raise ValueError(
                "slot_offset_y puts the slot too close to the outline edge"
            )


def build_stand(
    parameters: PixelPhotoStandParameters,
) -> cq.Workplane:
    """Solid pixel block with a leaning slot across it."""
    grid = parameters.grid

    body = grid.outline_prism(offset=0.0, height=parameters.height)
    body = grid.score_walls(
        body,
        height=parameters.height,
        depth=parameters.groove_depth,
        width=parameters.groove_width,
        levels=1,
    )

    margin = 1.0
    length = grid.width + 2 * margin
    cutter_height = parameters.slot_depth + margin

    # Build the slot upright with its floor at the slot bottom, then lean
    # it back (toward +Y) about the X axis through the slot floor.
    slot = (
        cq.Workplane("XY")
        .box(length, parameters.slot_width, cutter_height, centered=(True, True, False))
        .translate((0.0, 0.0, parameters.height - parameters.slot_depth))
    )
    pivot = (0.0, 0.0, parameters.height - parameters.slot_depth)
    slot = slot.rotate(pivot, (1.0, pivot[1], pivot[2]), -parameters.slot_tilt_degrees)
    slot = slot.translate((0.0, parameters.slot_offset_y, 0.0))

    return body.cut(slot)


def build_pixel_photo_stand(
    parameters: PixelPhotoStandParameters,
) -> ModelParts:
    """Build the single stand."""
    parameters.validate()

    return {"main": build_stand(parameters)}
