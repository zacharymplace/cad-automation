"""Gridfinity-inspired parametric empty bin shell."""

from dataclasses import dataclass

import cadquery as cq

from zcad.generators.gridfinity.specification import (
    GridfinitySpecification,
)


@dataclass(frozen=True)
class GridfinityBinParameters:
    """Parameters for a simple open-top bin."""

    cells_x: int
    cells_y: int
    height_units: int
    wall: float = 2.0
    floor: float = 2.0
    corner_radius: float = 3.0

    def validate(self) -> None:
        for name in (
            "cells_x",
            "cells_y",
            "height_units",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be greater than zero")

        for name in (
            "wall",
            "floor",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.corner_radius < 0:
            raise ValueError("corner_radius cannot be negative")


def build_gridfinity_bin(
    parameters: GridfinityBinParameters,
) -> cq.Workplane:
    """Build a simple specification-driven empty bin."""
    parameters.validate()

    specification = GridfinitySpecification()

    width = specification.cell_width(parameters.cells_x)
    depth = specification.cell_depth(parameters.cells_y)
    height = parameters.height_units * specification.height_unit

    if width <= 2 * parameters.wall:
        raise ValueError("Bin width must exceed twice the wall thickness")

    if depth <= 2 * parameters.wall:
        raise ValueError("Bin depth must exceed twice the wall thickness")

    if height <= parameters.floor:
        raise ValueError("Bin height must exceed floor thickness")

    outer = cq.Workplane("XY").box(
        width,
        depth,
        height,
    )

    inner = (
        cq.Workplane("XY")
        .workplane(offset=(-height / 2 + parameters.floor))
        .box(
            width - 2 * parameters.wall,
            depth - 2 * parameters.wall,
            height - parameters.floor + 1,
            centered=(True, True, False),
        )
    )

    model = outer.cut(inner)

    if parameters.corner_radius > 0:
        model = model.edges("|Z").fillet(parameters.corner_radius)

    return model
