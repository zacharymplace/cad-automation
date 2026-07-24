"""Printable Gridfinity compatibility coupon."""

from dataclasses import dataclass

import cadquery as cq

from zcad.generators.gridfinity.baseplate_socket import (
    GridfinitySocketParameters,
    build_gridfinity_socket,
)
from zcad.generators.gridfinity.mating_foot import (
    GridfinityMatingFootParameters,
    build_gridfinity_mating_foot,
)


@dataclass(frozen=True)
class GridfinityFitCouponParameters:
    """Parameters for a two-part foot and socket coupon."""

    plate_thickness: float = 6.0

    def validate(self) -> None:
        if self.plate_thickness <= 0:
            raise ValueError("plate_thickness must be greater than zero")


def build_gridfinity_fit_coupon(
    parameters: GridfinityFitCouponParameters,
) -> dict[str, cq.Workplane]:
    """Build separate mating-foot and socket coupon parts."""
    parameters.validate()

    return {
        "foot": build_gridfinity_mating_foot(GridfinityMatingFootParameters()),
        "socket": build_gridfinity_socket(
            GridfinitySocketParameters(plate_thickness=parameters.plate_thickness)
        ),
    }
