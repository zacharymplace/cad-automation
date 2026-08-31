"""Parametric sink-edge caddy for a sponge and one or more scrub brushes.

Shares its drainage mechanism with `drip_tray`: a raised rack keeps the
sponge and brushes out of standing water, resting on top of the same
`drainage_basin` that carries drips down a sloped floor and out an open
spout into the sink. What differs is what sits on top -- instead of a
uniform perforated grid, the rack has a slot sized to hold a sponge on
edge, one or more round holes for brush handles, and drainage holes
filling whatever flat area is left.
"""

import math
from dataclasses import dataclass, fields

import cadquery as cq

from zcad.generators.drainage_basin import (
    DrainageBasinParameters,
    build_drainage_basin,
)

ModelParts = dict[str, cq.Workplane]

_BASIN_FIELD_NAMES = {field.name for field in fields(DrainageBasinParameters)}


@dataclass(frozen=True)
class SpongeCaddyParameters:
    """Dimensions for the basin body and its sponge-and-brush rack."""

    width: float
    depth: float
    wall: float = 3.0
    basin_height: float = 16.0
    floor_back: float = 6.0
    floor_front: float = 2.6
    spout_length: float = 30.0
    spout_tip_thickness: float = 1.4
    spout_flare_margin: float = 15.0
    spout_tip_bulge: float = 0.0
    spout_tip_fillet: float = 6.0
    corner_radius: float = 5.0

    drip_groove: bool = True
    groove_depth: float = 0.5
    groove_width: float = 2.0
    groove_offset_from_tip: float = 5.0

    label: str = "Z$ CAD"
    label_size: float = 4.0
    label_height: float = 0.4

    rack_thickness: float = 3.0
    rack_edge_margin: float = 8.0
    rack_hole_diameter: float = 6.0
    rack_hole_spacing: float = 14.0
    rack_clearance: float = 1.0

    sponge_slot_length: float = 80.0
    sponge_slot_width: float = 18.0
    sponge_slot_center_x: float = -40.0

    brush_hole_diameter: float = 30.0
    brush_hole_count: int = 2
    brush_hole_spacing: float = 38.0
    brush_holes_center_x: float = 40.0

    def basin_parameters(self) -> DrainageBasinParameters:
        """The subset of fields the shared drainage basin needs."""
        values = {
            name: getattr(self, name)
            for name in _BASIN_FIELD_NAMES
            if hasattr(self, name)
        }
        return DrainageBasinParameters(**values)

    def brush_hole_positions(self) -> list[tuple[float, float]]:
        """Center points of each brush hole, evenly spaced and centered
        on `brush_holes_center_x`."""
        start = self.brush_holes_center_x - (self.brush_hole_count - 1) * (
            self.brush_hole_spacing / 2
        )
        return [
            (start + index * self.brush_hole_spacing, 0.0)
            for index in range(self.brush_hole_count)
        ]

    def validate(self) -> None:
        self.basin_parameters().validate()

        positive_values = {
            "rack_thickness": self.rack_thickness,
            "rack_edge_margin": self.rack_edge_margin,
            "rack_hole_diameter": self.rack_hole_diameter,
            "rack_hole_spacing": self.rack_hole_spacing,
            "sponge_slot_length": self.sponge_slot_length,
            "sponge_slot_width": self.sponge_slot_width,
            "brush_hole_diameter": self.brush_hole_diameter,
            "brush_hole_spacing": self.brush_hole_spacing,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.rack_clearance < 0:
            raise ValueError("rack_clearance cannot be negative")

        if self.brush_hole_count < 1:
            raise ValueError("brush_hole_count must be at least one")

        if self.rack_hole_diameter >= self.rack_hole_spacing:
            raise ValueError(
                "rack_hole_diameter must be smaller than rack_hole_spacing"
            )

        interior_width = self.width - 2 * self.wall
        interior_depth = self.depth - self.wall

        if 2 * self.rack_edge_margin >= interior_width:
            raise ValueError("rack_edge_margin leaves no room across the width")

        if 2 * self.rack_edge_margin >= interior_depth:
            raise ValueError("rack_edge_margin leaves no room across the depth")

        slot_half_width = self.sponge_slot_width / 2
        slot_left = self.sponge_slot_center_x - slot_half_width
        slot_right = self.sponge_slot_center_x + slot_half_width

        if abs(self.sponge_slot_center_x) + slot_half_width >= self.width / 2:
            raise ValueError("sponge_slot_center_x places the slot outside the rack")

        if self.sponge_slot_length >= self.depth:
            raise ValueError("sponge_slot_length must be smaller than depth")

        brush_positions = self.brush_hole_positions()
        brush_radius = self.brush_hole_diameter / 2

        for x, _ in brush_positions:
            if abs(x) + brush_radius >= self.width / 2:
                raise ValueError(
                    "brush hole layout places a hole outside the rack"
                )

            if slot_left - brush_radius < x < slot_right + brush_radius:
                raise ValueError("brush holes overlap the sponge slot")


def _build_rack(
    parameters: SpongeCaddyParameters,
) -> cq.Workplane:
    """Build the rack: a sponge slot, brush holes, and drainage holes
    filling the rest, on a plate that rests on top of the basin walls."""
    plate = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.rack_thickness,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        plate = plate.edges("|Z").fillet(parameters.corner_radius)

    cut_height = parameters.rack_thickness + 2

    slot = (
        cq.Workplane("XY")
        .workplane(offset=-1)
        .center(parameters.sponge_slot_center_x, 0)
        .rect(parameters.sponge_slot_width, parameters.sponge_slot_length)
        .extrude(cut_height)
    )
    plate = plate.cut(slot)

    brush_positions = parameters.brush_hole_positions()

    brush_holes = (
        cq.Workplane("XY")
        .workplane(offset=-1)
        .pushPoints(brush_positions)
        .circle(parameters.brush_hole_diameter / 2)
        .extrude(cut_height)
    )
    plate = plate.cut(brush_holes)

    usable_width = parameters.width - 2 * parameters.rack_edge_margin
    usable_depth = parameters.depth - 2 * parameters.rack_edge_margin

    count_x = max(int(usable_width // parameters.rack_hole_spacing) + 1, 1)
    count_y = max(int(usable_depth // parameters.rack_hole_spacing) + 1, 1)

    span_x = (count_x - 1) * parameters.rack_hole_spacing
    span_y = (count_y - 1) * parameters.rack_hole_spacing

    hole_radius = parameters.rack_hole_diameter / 2
    slot_keepout_x = parameters.sponge_slot_width / 2 + hole_radius + parameters.rack_clearance
    slot_keepout_y = parameters.sponge_slot_length / 2 + hole_radius + parameters.rack_clearance
    brush_keepout = parameters.brush_hole_diameter / 2 + hole_radius + parameters.rack_clearance

    def blocked(x: float, y: float) -> bool:
        if (
            abs(x - parameters.sponge_slot_center_x) < slot_keepout_x
            and abs(y) < slot_keepout_y
        ):
            return True

        return any(
            math.hypot(x - bx, y - by) < brush_keepout for bx, by in brush_positions
        )

    points = [
        (
            -span_x / 2 + i * parameters.rack_hole_spacing,
            -span_y / 2 + j * parameters.rack_hole_spacing,
        )
        for i in range(count_x)
        for j in range(count_y)
        if not blocked(
            -span_x / 2 + i * parameters.rack_hole_spacing,
            -span_y / 2 + j * parameters.rack_hole_spacing,
        )
    ]

    if points:
        drain_holes = (
            cq.Workplane("XY")
            .workplane(offset=-1)
            .pushPoints(points)
            .circle(hole_radius)
            .extrude(cut_height)
        )
        plate = plate.cut(drain_holes)

    return plate


def build_sponge_caddy(
    parameters: SpongeCaddyParameters,
) -> ModelParts:
    """Build the basin and its sponge-and-brush rack."""
    parameters.validate()

    return {
        "basin": build_drainage_basin(parameters.basin_parameters()),
        "rack": _build_rack(parameters),
    }
