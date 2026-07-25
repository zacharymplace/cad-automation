"""Parametric multi-part electronics enclosure."""

from dataclasses import dataclass

import cadquery as cq
from zcad_core.features import (
    InsertBossParameters,
    add_heat_set_insert_boss,
)
from zcad_core.features.labels import add_embossed_label
from zcad_core.hardware import (
    BoardEdge,
    get_fastener,
)


@dataclass(frozen=True)
class EnclosureParameters:
    """Dimensions for an enclosure body and removable lid."""

    width: float
    depth: float
    height: float
    wall: float = 3.0
    floor: float = 3.0

    lid_thickness: float = 3.0
    lid_clearance: float = 0.25
    lid_lip_height: float = 4.0
    lid_lip_wall: float = 2.0

    corner_radius: float = 4.0

    cable_slot_width: float = 14.0
    cable_slot_height: float = 8.0
    cable_slot_edge: BoardEdge = "negative_y"
    cable_slot_center_offset: float = 0.0
    cable_slot_bottom_offset: float = 0.0

    mounting_hole_diameter: float = 3.2
    mounting_hole_spacing_x: float = 60.0
    mounting_hole_spacing_y: float = 35.0

    label: str = "Z$ CAD"
    label_size: float = 6.0
    label_height: float = 0.6

    corner_insert_fastener: str | None = None
    corner_insert_wall_mm: float = 1.8
    corner_insert_edge_offset_mm: float = 10.0

    def validate(self) -> None:
        positive_values = {
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "wall": self.wall,
            "floor": self.floor,
            "lid_thickness": self.lid_thickness,
            "lid_lip_height": self.lid_lip_height,
            "lid_lip_wall": self.lid_lip_wall,
            "cable_slot_width": self.cable_slot_width,
            "cable_slot_height": self.cable_slot_height,
            "mounting_hole_diameter": self.mounting_hole_diameter,
            "label_size": self.label_size,
            "label_height": self.label_height,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.lid_clearance < 0:
            raise ValueError("lid_clearance cannot be negative")

        if self.corner_radius < 0:
            raise ValueError("corner_radius cannot be negative")

        if not self.label.strip():
            raise ValueError("label cannot be empty")

        if self.corner_insert_wall_mm <= 0:
            raise ValueError("corner_insert_wall_mm must be greater than zero")

        if self.corner_insert_edge_offset_mm <= 0:
            raise ValueError("corner_insert_edge_offset_mm must be greater than zero")

        if self.width <= 2 * self.wall:
            raise ValueError("width must exceed twice the wall thickness")

        if self.depth <= 2 * self.wall:
            raise ValueError("depth must exceed twice the wall thickness")

        if self.height <= self.floor:
            raise ValueError("height must exceed floor thickness")

        inner_width = self.width - 2 * self.wall
        inner_depth = self.depth - 2 * self.wall

        supported_edges = {
            "negative_x",
            "positive_x",
            "negative_y",
            "positive_y",
        }

        if self.cable_slot_edge not in supported_edges:
            raise ValueError(f"unsupported cable_slot_edge: {self.cable_slot_edge}")

        if self.cable_slot_bottom_offset < 0:
            raise ValueError("cable_slot_bottom_offset cannot be negative")

        if self.cable_slot_edge in {
            "negative_y",
            "positive_y",
        }:
            available_slot_span = inner_width
        else:
            available_slot_span = inner_depth

        if self.cable_slot_width >= available_slot_span:
            raise ValueError(
                "cable_slot_width must be smaller than the selected wall span"
            )

        inner_height = self.height - self.floor

        if self.cable_slot_bottom_offset + self.cable_slot_height > inner_height:
            raise ValueError("cable slot must fit within the enclosure cavity height")

        maximum_center_offset = (available_slot_span - self.cable_slot_width) / 2

        if abs(self.cable_slot_center_offset) > maximum_center_offset:
            raise ValueError(
                "cable_slot_center_offset places the slot outside the selected wall"
            )

        lip_outer_width = inner_width - 2 * self.lid_clearance
        lip_outer_depth = inner_depth - 2 * self.lid_clearance

        if lip_outer_width <= 2 * self.lid_lip_wall:
            raise ValueError("lid lip leaves no internal width")

        if lip_outer_depth <= 2 * self.lid_lip_wall:
            raise ValueError("lid lip leaves no internal depth")

        maximum_hole_x = self.width / 2 - self.wall - self.mounting_hole_diameter / 2
        maximum_hole_y = self.depth / 2 - self.wall - self.mounting_hole_diameter / 2

        if self.mounting_hole_spacing_x / 2 > maximum_hole_x:
            raise ValueError("mounting_hole_spacing_x places holes outside the floor")

        if self.mounting_hole_spacing_y / 2 > maximum_hole_y:
            raise ValueError("mounting_hole_spacing_y places holes outside the floor")


def _build_body(
    parameters: EnclosureParameters,
) -> cq.Workplane:
    """Build the open enclosure body."""
    outer = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.height,
    )

    inner_width = parameters.width - 2 * parameters.wall
    inner_depth = parameters.depth - 2 * parameters.wall
    inner_height = parameters.height - parameters.floor

    inner_bottom_z = -parameters.height / 2 + parameters.floor

    inner = (
        cq.Workplane("XY")
        .workplane(offset=inner_bottom_z)
        .box(
            inner_width,
            inner_depth,
            inner_height + 1,
            centered=(
                True,
                True,
                False,
            ),
        )
    )

    body = outer.cut(inner)

    if parameters.corner_radius > 0:
        body = body.edges("|Z").fillet(parameters.corner_radius)

    cable_slot_z = (
        -parameters.height / 2
        + parameters.floor
        + parameters.cable_slot_bottom_offset
        + parameters.cable_slot_height / 2
    )

    if parameters.cable_slot_edge in {
        "negative_y",
        "positive_y",
    }:
        cutter_width = parameters.cable_slot_width
        cutter_depth = parameters.wall * 4
        cable_slot_x = parameters.cable_slot_center_offset
        cable_slot_y = (
            -parameters.depth / 2
            if parameters.cable_slot_edge == "negative_y"
            else parameters.depth / 2
        )
    else:
        cutter_width = parameters.wall * 4
        cutter_depth = parameters.cable_slot_width
        cable_slot_x = (
            -parameters.width / 2
            if parameters.cable_slot_edge == "negative_x"
            else parameters.width / 2
        )
        cable_slot_y = parameters.cable_slot_center_offset

    cable_cutter = (
        cq.Workplane("XY")
        .box(
            cutter_width,
            cutter_depth,
            parameters.cable_slot_height,
        )
        .translate(
            (
                cable_slot_x,
                cable_slot_y,
                cable_slot_z,
            )
        )
    )

    body = body.cut(cable_cutter)

    hole_points = [
        (
            -parameters.mounting_hole_spacing_x / 2,
            -parameters.mounting_hole_spacing_y / 2,
        ),
        (
            parameters.mounting_hole_spacing_x / 2,
            -parameters.mounting_hole_spacing_y / 2,
        ),
        (
            -parameters.mounting_hole_spacing_x / 2,
            parameters.mounting_hole_spacing_y / 2,
        ),
        (
            parameters.mounting_hole_spacing_x / 2,
            parameters.mounting_hole_spacing_y / 2,
        ),
    ]

    hole_cutter = (
        cq.Workplane("XY")
        .workplane(offset=(-parameters.height / 2 - 1))
        .pushPoints(hole_points)
        .circle(parameters.mounting_hole_diameter / 2)
        .extrude(parameters.floor + 2)
    )

    body = body.cut(hole_cutter)

    if parameters.corner_insert_fastener is None:
        return body

    fastener = get_fastener(
        parameters.corner_insert_fastener,
    )

    boss_radius = (
        fastener.heat_set_insert_diameter_mm + 2 * parameters.corner_insert_wall_mm
    ) / 2

    x = parameters.width / 2 - parameters.wall - parameters.corner_insert_edge_offset_mm
    y = parameters.depth / 2 - parameters.wall - parameters.corner_insert_edge_offset_mm

    if x <= boss_radius:
        raise ValueError("corner insert bosses do not fit within enclosure width")

    if y <= boss_radius:
        raise ValueError("corner insert bosses do not fit within enclosure depth")

    base_z_mm = -parameters.height / 2

    for boss_x, boss_y in (
        (-x, -y),
        (x, -y),
        (-x, y),
        (x, y),
    ):
        body = add_heat_set_insert_boss(
            body,
            parameters=InsertBossParameters.from_fastener(
                fastener=fastener,
                x=boss_x,
                y=boss_y,
                base_z_mm=base_z_mm,
                base_height_mm=parameters.floor,
                radial_wall_mm=parameters.corner_insert_wall_mm,
            ),
        )

    return body


def _build_lid(
    parameters: EnclosureParameters,
) -> cq.Workplane:
    """Build the removable enclosure lid."""
    lid = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.lid_thickness,
    )

    if parameters.corner_radius > 0:
        lid = lid.edges("|Z").fillet(parameters.corner_radius)

    inner_width = parameters.width - 2 * parameters.wall
    inner_depth = parameters.depth - 2 * parameters.wall

    lip_outer_width = inner_width - 2 * parameters.lid_clearance
    lip_outer_depth = inner_depth - 2 * parameters.lid_clearance

    lip_inner_width = lip_outer_width - 2 * parameters.lid_lip_wall
    lip_inner_depth = lip_outer_depth - 2 * parameters.lid_lip_wall

    lip_center_z = -parameters.lid_thickness / 2 - parameters.lid_lip_height / 2

    lip_outer = (
        cq.Workplane("XY")
        .box(
            lip_outer_width,
            lip_outer_depth,
            parameters.lid_lip_height,
        )
        .translate(
            (
                0,
                0,
                lip_center_z,
            )
        )
    )

    lip_inner = (
        cq.Workplane("XY")
        .box(
            lip_inner_width,
            lip_inner_depth,
            parameters.lid_lip_height + 2,
        )
        .translate(
            (
                0,
                0,
                lip_center_z,
            )
        )
    )

    lip_ring = lip_outer.cut(lip_inner)
    lid = lid.union(lip_ring)

    return add_embossed_label(
        lid,
        text=parameters.label,
        x=0,
        y=0,
        base_height=parameters.lid_thickness,
        text_size=parameters.label_size,
        emboss_height=parameters.label_height,
    )


def build_enclosure(
    parameters: EnclosureParameters,
) -> dict[str, cq.Workplane]:
    """Build and return the enclosure body and lid."""
    parameters.validate()

    return {
        "body": _build_body(parameters),
        "lid": _build_lid(parameters),
    }
