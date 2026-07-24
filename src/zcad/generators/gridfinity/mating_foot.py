"""Gridfinity mating-foot geometry."""

from dataclasses import dataclass

import cadquery as cq

from zcad.generators.gridfinity.specification import (
    GridfinitySpecification,
)


@dataclass(frozen=True)
class GridfinityMatingFootParameters:
    """Parameters for one Gridfinity mating foot."""

    cells_x: int = 1
    cells_y: int = 1

    def validate(self) -> None:
        if self.cells_x <= 0:
            raise ValueError("cells_x must be greater than zero")

        if self.cells_y <= 0:
            raise ValueError("cells_y must be greater than zero")


def build_gridfinity_mating_foot(
    parameters: GridfinityMatingFootParameters,
) -> cq.Workplane:
    """Build a stepped mating-foot approximation."""
    parameters.validate()

    specification = GridfinitySpecification()

    cell_width = specification.grid_pitch
    outer_width = cell_width - 2 * specification.bin_mating_inset

    lower_height = specification.bottom_chamfer
    middle_height = specification.bin_mating_depth - lower_height

    if middle_height <= 0:
        raise ValueError("Mating profile heights are invalid")

    foot = cq.Workplane("XY")

    for x_index in range(parameters.cells_x):
        for y_index in range(parameters.cells_y):
            x = (x_index - (parameters.cells_x - 1) / 2) * specification.grid_pitch

            y = (y_index - (parameters.cells_y - 1) / 2) * specification.grid_pitch

            lower = (
                cq.Workplane("XY")
                .center(x, y)
                .rect(
                    outer_width - 2 * lower_height,
                    outer_width - 2 * lower_height,
                )
                .extrude(lower_height)
                .edges("|Z")
                .chamfer(lower_height)
            )

            upper = (
                cq.Workplane("XY")
                .workplane(offset=lower_height)
                .center(x, y)
                .rect(
                    outer_width,
                    outer_width,
                )
                .extrude(middle_height)
            )

            foot = foot.union(lower).union(upper)

    return foot
