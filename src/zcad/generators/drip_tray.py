"""Parametric sink-edge drip tray for liquid soap dispensers.

A raised, perforated grid keeps the dispenser's base out of standing
water, resting on top of a shared `drainage_basin` that carries drips
down a sloped floor and out an open spout into the sink. See
`zcad.generators.drainage_basin` for how the basin itself works.
"""

from dataclasses import dataclass, fields

import cadquery as cq

from zcad.generators.drainage_basin import (
    DrainageBasinParameters,
    build_drainage_basin,
)

ModelParts = dict[str, cq.Workplane]

_BASIN_FIELD_NAMES = {field.name for field in fields(DrainageBasinParameters)}


@dataclass(frozen=True)
class DripTrayParameters:
    """Dimensions for the basin body and its perforated grid insert."""

    width: float
    depth: float
    wall: float = 3.0
    basin_height: float = 14.0
    floor_back: float = 5.0
    floor_front: float = 2.4
    spout_length: float = 28.0
    spout_tip_thickness: float = 1.4
    spout_flare_margin: float = 15.0
    spout_tip_bulge: float = 0.0
    spout_tip_fillet: float = 6.0
    corner_radius: float = 5.0

    drip_groove: bool = True
    groove_depth: float = 0.5
    groove_width: float = 2.0
    groove_offset_from_tip: float = 5.0

    grid_thickness: float = 3.0
    grid_hole_diameter: float = 6.0
    grid_hole_spacing: float = 12.0
    grid_edge_margin: float = 8.0

    label: str = "Z$ CAD"
    label_size: float = 4.0
    label_height: float = 0.4

    def basin_parameters(self) -> DrainageBasinParameters:
        """The subset of fields the shared drainage basin needs."""
        values = {
            name: getattr(self, name)
            for name in _BASIN_FIELD_NAMES
            if hasattr(self, name)
        }
        return DrainageBasinParameters(**values)

    def validate(self) -> None:
        self.basin_parameters().validate()

        positive_values = {
            "grid_thickness": self.grid_thickness,
            "grid_hole_diameter": self.grid_hole_diameter,
            "grid_hole_spacing": self.grid_hole_spacing,
            "grid_edge_margin": self.grid_edge_margin,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.grid_hole_diameter >= self.grid_hole_spacing:
            raise ValueError(
                "grid_hole_diameter must be smaller than grid_hole_spacing"
            )

        interior_width = self.width - 2 * self.wall
        interior_depth = self.depth - self.wall

        if 2 * self.grid_edge_margin >= interior_width:
            raise ValueError("grid_edge_margin leaves no room across the width")

        if 2 * self.grid_edge_margin >= interior_depth:
            raise ValueError("grid_edge_margin leaves no room across the depth")


def _build_grid(
    parameters: DripTrayParameters,
) -> cq.Workplane:
    """Build the perforated grid that rests on top of the basin walls."""
    plate = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.grid_thickness,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        plate = plate.edges("|Z").fillet(parameters.corner_radius)

    usable_width = parameters.width - 2 * parameters.grid_edge_margin
    usable_depth = parameters.depth - 2 * parameters.grid_edge_margin

    count_x = max(int(usable_width // parameters.grid_hole_spacing) + 1, 1)
    count_y = max(int(usable_depth // parameters.grid_hole_spacing) + 1, 1)

    span_x = (count_x - 1) * parameters.grid_hole_spacing
    span_y = (count_y - 1) * parameters.grid_hole_spacing

    points = [
        (
            -span_x / 2 + i * parameters.grid_hole_spacing,
            -span_y / 2 + j * parameters.grid_hole_spacing,
        )
        for i in range(count_x)
        for j in range(count_y)
    ]

    holes = (
        cq.Workplane("XY")
        .workplane(offset=-1)
        .pushPoints(points)
        .circle(parameters.grid_hole_diameter / 2)
        .extrude(parameters.grid_thickness + 2)
    )

    return plate.cut(holes)


def build_drip_tray(
    parameters: DripTrayParameters,
) -> ModelParts:
    """Build the basin and its perforated grid insert."""
    parameters.validate()

    return {
        "basin": build_drainage_basin(parameters.basin_parameters()),
        "grid": _build_grid(parameters),
    }
