"""Parametric sink-edge drip tray for liquid soap dispensers.

A raised, perforated grid keeps the dispenser's base out of standing
water. Drips fall through the grid onto a basin floor that tapers
continuously from the back wall down to an open, wall-less spout that
cantilevers past the counter edge, so collected water releases directly
into the sink instead of pooling under the dispenser.
"""

import math
from dataclasses import dataclass

import cadquery as cq

ModelParts = dict[str, cq.Workplane]


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
    corner_radius: float = 5.0

    drip_groove: bool = True
    groove_depth: float = 0.5
    groove_width: float = 2.0
    groove_offset_from_tip: float = 5.0

    grid_thickness: float = 3.0
    grid_hole_diameter: float = 6.0
    grid_hole_spacing: float = 12.0
    grid_edge_margin: float = 8.0

    def validate(self) -> None:
        positive_values = {
            "width": self.width,
            "depth": self.depth,
            "wall": self.wall,
            "basin_height": self.basin_height,
            "floor_back": self.floor_back,
            "floor_front": self.floor_front,
            "spout_length": self.spout_length,
            "spout_tip_thickness": self.spout_tip_thickness,
            "grid_thickness": self.grid_thickness,
            "grid_hole_diameter": self.grid_hole_diameter,
            "grid_hole_spacing": self.grid_hole_spacing,
            "grid_edge_margin": self.grid_edge_margin,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.corner_radius < 0:
            raise ValueError("corner_radius cannot be negative")

        if self.width <= 2 * self.wall:
            raise ValueError("width must exceed twice the wall thickness")

        if self.depth <= self.wall:
            raise ValueError("depth must exceed the back wall thickness")

        if self.basin_height <= self.floor_back:
            raise ValueError("basin_height must exceed floor_back")

        if self.floor_front >= self.floor_back:
            raise ValueError(
                "floor_front must be less than floor_back so the basin "
                "floor slopes down toward the spout"
            )

        if self.spout_tip_thickness >= self.floor_front:
            raise ValueError(
                "spout_tip_thickness must be less than floor_front so the "
                "spout keeps tapering down to a thin drip edge"
            )

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

        if self.drip_groove:
            if self.groove_offset_from_tip >= self.spout_length:
                raise ValueError(
                    "groove_offset_from_tip must be less than spout_length"
                )

            if self.groove_depth >= self.spout_tip_thickness:
                raise ValueError("groove_depth must be less than spout_tip_thickness")


def _slope_cutter(
    *,
    span_width: float,
    run: float,
    height: float,
    slack: float = 10.0,
) -> cq.Workplane:
    """A box pivoted at the local origin with its bottom face in the z=0
    plane, ready to be rotated about the X axis into a tapered cutting
    tool and translated into place."""
    length = run + 2 * slack

    return (
        cq.Workplane("XY")
        .box(span_width, length, height, centered=(True, True, False))
        .translate((0, run / 2, 0))
    )


def _build_basin(
    parameters: DripTrayParameters,
) -> cq.Workplane:
    """Build the basin with a continuously sloped, wall-less spout."""
    interior_width = parameters.width - 2 * parameters.wall

    y_back = -parameters.depth / 2 + parameters.wall
    y_front = parameters.depth / 2
    y_tip = parameters.depth / 2 + parameters.spout_length

    outer = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.basin_height,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        outer = outer.edges("|Z and <Y").fillet(parameters.corner_radius)

    spout_blank = (
        cq.Workplane("XY")
        .box(
            interior_width,
            parameters.spout_length,
            parameters.floor_front,
            centered=(True, False, False),
        )
        .translate((0, y_front, 0))
    )

    blank = outer.union(spout_blank)

    basin_run = y_front - y_back
    basin_drop = parameters.floor_back - parameters.floor_front
    basin_angle = math.degrees(math.atan2(basin_drop, basin_run))

    basin_cutter = _slope_cutter(
        span_width=interior_width,
        run=basin_run,
        height=parameters.basin_height + 20,
    )
    basin_cutter = basin_cutter.rotate((0, 0, 0), (1, 0, 0), -basin_angle).translate(
        (0, y_back, parameters.floor_back)
    )

    spout_run = y_tip - y_front
    spout_drop = parameters.floor_front - parameters.spout_tip_thickness
    spout_angle = math.degrees(math.atan2(spout_drop, spout_run))

    spout_cutter = _slope_cutter(
        span_width=interior_width,
        run=spout_run,
        height=parameters.basin_height + 20,
        slack=2.0,
    )
    spout_cutter = spout_cutter.rotate((0, 0, 0), (1, 0, 0), -spout_angle).translate(
        (0, y_front, parameters.floor_front)
    )

    body = blank.cut(basin_cutter).cut(spout_cutter)

    if parameters.drip_groove:
        y_groove = y_tip - parameters.groove_offset_from_tip

        groove = (
            cq.Workplane("XY")
            .box(
                interior_width + 4,
                parameters.groove_width,
                parameters.groove_depth + 1.0,
                centered=(True, True, False),
            )
            .translate((0, y_groove - parameters.groove_width / 2, -1.0))
        )

        body = body.cut(groove)

    return body


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
        "basin": _build_basin(parameters),
        "grid": _build_grid(parameters),
    }
