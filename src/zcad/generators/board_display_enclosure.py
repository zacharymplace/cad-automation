"""Generate printable enclosures from board-display designs."""

from dataclasses import dataclass

import cadquery as cq
from zcad_core.assemblies import (
    derive_enclosure_specification,
)

from zcad.designs import (
    BoardDisplayDesign,
    build_board_display_design,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
    build_enclosure,
)


@dataclass(frozen=True)
class BoardDisplayEnclosureParameters:
    """Manufacturing policy for a board-display enclosure."""

    wall_mm: float = 3.0
    floor_mm: float = 3.0

    lid_thickness_mm: float = 3.0
    lid_clearance_mm: float = 0.25
    lid_lip_height_mm: float = 4.0
    lid_lip_wall_mm: float = 2.0

    internal_clearance_mm: float = 2.0
    connector_cutout_clearance_mm: float = 0.5

    corner_radius_mm: float = 4.0

    mounting_hole_diameter_mm: float = 3.2
    mounting_hole_edge_offset_mm: float = 7.0

    label: str = "Z$ CAD"
    label_size_mm: float = 6.0
    label_height_mm: float = 0.6

    def validate(self) -> None:
        """Validate enclosure manufacturing policy."""
        positive_values = {
            "wall_mm": self.wall_mm,
            "floor_mm": self.floor_mm,
            "lid_thickness_mm": self.lid_thickness_mm,
            "lid_lip_height_mm": self.lid_lip_height_mm,
            "lid_lip_wall_mm": self.lid_lip_wall_mm,
            "mounting_hole_diameter_mm": (self.mounting_hole_diameter_mm),
            "mounting_hole_edge_offset_mm": (self.mounting_hole_edge_offset_mm),
            "label_size_mm": self.label_size_mm,
            "label_height_mm": self.label_height_mm,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        non_negative_values = {
            "lid_clearance_mm": self.lid_clearance_mm,
            "internal_clearance_mm": (self.internal_clearance_mm),
            "connector_cutout_clearance_mm": (self.connector_cutout_clearance_mm),
            "corner_radius_mm": self.corner_radius_mm,
        }

        for name, value in non_negative_values.items():
            if value < 0:
                raise ValueError(f"{name} must not be negative")

        if not self.label.strip():
            raise ValueError("label must not be empty")


def _mounting_hole_spacing(
    *,
    outer_size_mm: float,
    wall_mm: float,
    hole_diameter_mm: float,
    edge_offset_mm: float,
) -> float:
    """Resolve symmetric mounting-hole spacing inside one axis."""
    maximum_center_offset_mm = outer_size_mm / 2 - wall_mm - hole_diameter_mm / 2

    requested_center_offset_mm = outer_size_mm / 2 - edge_offset_mm

    center_offset_mm = min(
        maximum_center_offset_mm,
        requested_center_offset_mm,
    )

    if center_offset_mm <= 0:
        raise ValueError("mounting-hole policy leaves no valid center offset")

    return 2 * center_offset_mm


def _build_enclosure_parameters(
    design: BoardDisplayDesign,
    policy: BoardDisplayEnclosureParameters,
) -> EnclosureParameters:
    """Resolve existing enclosure parameters from a design and policy."""
    policy.validate()

    assembly = build_board_display_design(design)

    specification = derive_enclosure_specification(
        assembly,
        internal_clearance_mm=(policy.internal_clearance_mm),
        connector_cutout_clearance_mm=(policy.connector_cutout_clearance_mm),
    )

    width_mm = specification.inner_width_mm + 2 * policy.wall_mm
    depth_mm = specification.inner_depth_mm + 2 * policy.wall_mm
    height_mm = specification.inner_height_mm + policy.floor_mm

    mounting_hole_spacing_x_mm = _mounting_hole_spacing(
        outer_size_mm=width_mm,
        wall_mm=policy.wall_mm,
        hole_diameter_mm=(policy.mounting_hole_diameter_mm),
        edge_offset_mm=(policy.mounting_hole_edge_offset_mm),
    )
    mounting_hole_spacing_y_mm = _mounting_hole_spacing(
        outer_size_mm=depth_mm,
        wall_mm=policy.wall_mm,
        hole_diameter_mm=(policy.mounting_hole_diameter_mm),
        edge_offset_mm=(policy.mounting_hole_edge_offset_mm),
    )

    return EnclosureParameters(
        width=width_mm,
        depth=depth_mm,
        height=height_mm,
        wall=policy.wall_mm,
        floor=policy.floor_mm,
        lid_thickness=policy.lid_thickness_mm,
        lid_clearance=policy.lid_clearance_mm,
        lid_lip_height=policy.lid_lip_height_mm,
        lid_lip_wall=policy.lid_lip_wall_mm,
        corner_radius=policy.corner_radius_mm,
        cable_slot_width=(specification.cable_width_mm),
        cable_slot_height=(specification.cable_height_mm),
        cable_slot_edge=specification.cable_edge,
        cable_slot_center_offset=(specification.cable_center_offset_mm),
        cable_slot_bottom_offset=(
            specification.cable_bottom_z_mm - specification.bottom_z_mm
        ),
        mounting_hole_diameter=(policy.mounting_hole_diameter_mm),
        mounting_hole_spacing_x=(mounting_hole_spacing_x_mm),
        mounting_hole_spacing_y=(mounting_hole_spacing_y_mm),
        label=policy.label,
        label_size=policy.label_size_mm,
        label_height=policy.label_height_mm,
    )


def build_board_display_enclosure(
    design: BoardDisplayDesign,
    parameters: BoardDisplayEnclosureParameters | None = None,
) -> dict[str, cq.Workplane]:
    """Build printable body and lid parts for a board-display design."""
    resolved = (
        parameters
        if parameters is not None
        else BoardDisplayEnclosureParameters(
            label=design.product,
        )
    )

    enclosure_parameters = _build_enclosure_parameters(
        design,
        resolved,
    )

    return build_enclosure(enclosure_parameters)
