"""Approximate Gridfinity baseplate socket."""

from dataclasses import dataclass

import cadquery as cq

from zcad.generators.gridfinity.specification import (
    GridfinitySpecification,
)


@dataclass(frozen=True)
class GridfinitySocketParameters:
    """Parameters for a one-cell socket coupon."""

    cells_x: int = 1
    cells_y: int = 1
    plate_thickness: float = 6.0

    def validate(self) -> None:
        if self.cells_x <= 0:
            raise ValueError("cells_x must be greater than zero")

        if self.cells_y <= 0:
            raise ValueError("cells_y must be greater than zero")

        if self.plate_thickness <= 0:
            raise ValueError("plate_thickness must be greater than zero")


def build_gridfinity_socket(
    parameters: GridfinitySocketParameters,
) -> cq.Workplane:
    """Build a simple mating socket coupon."""
    parameters.validate()

    spec = GridfinitySpecification()

    width = parameters.cells_x * spec.grid_pitch

    depth = parameters.cells_y * spec.grid_pitch

    body = cq.Workplane("XY").box(
        width,
        depth,
        parameters.plate_thickness,
    )

    pocket_width = spec.grid_pitch - 2 * spec.baseplate_mating_inset

    pocket_depth = pocket_width

    pocket = (
        cq.Workplane("XY")
        .workplane(
            offset=(parameters.plate_thickness / 2 - spec.baseplate_mating_depth)
        )
        .box(
            pocket_width,
            pocket_depth,
            spec.baseplate_mating_depth + 1,
            centered=(
                True,
                True,
                False,
            ),
        )
    )

    return body.cut(pocket)
