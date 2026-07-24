"""Parametric multi-part electronics enclosure."""

from dataclasses import dataclass

import cadquery as cq

from zcad.features.labels import add_embossed_label


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

    mounting_hole_diameter: float = 3.2
    mounting_hole_spacing_x: float = 60.0
    mounting_hole_spacing_y: float = 35.0

    label: str = "Z$ CAD"
    label_size: float = 6.0
    label_height: float = 0.6

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

        if self.width <= 2 * self.wall:
            raise ValueError("width must exceed twice the wall thickness")

        if self.depth <= 2 * self.wall:
            raise ValueError("depth must exceed twice the wall thickness")

        if self.height <= self.floor:
            raise ValueError("height must exceed floor thickness")

        inner_width = self.width - 2 * self.wall
        inner_depth = self.depth - 2 * self.wall

        if self.cable_slot_width >= inner_width:
            raise ValueError("cable_slot_width must be smaller than inner width")

        if self.cable_slot_height >= self.height:
            raise ValueError("cable_slot_height must be smaller than enclosure height")

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

    cable_slot_z = parameters.height / 2 - parameters.cable_slot_height / 2

    cable_cutter = (
        cq.Workplane("XY")
        .box(
            parameters.cable_slot_width,
            parameters.wall * 4,
            parameters.cable_slot_height,
        )
        .translate(
            (
                0,
                -parameters.depth / 2,
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

    return body.cut(hole_cutter)


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
