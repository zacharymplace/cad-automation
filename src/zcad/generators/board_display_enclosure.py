"""Generate printable enclosures from board-display designs."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

import cadquery as cq
from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureBoundary,
    EnclosureSpecification,
    InterferenceFinding,
    InterferenceReport,
    analyze_boundary_clearance,
    assembly_mounting_hole_positions,
    derive_enclosure_specification,
)
from zcad_core.features import (
    PcbStandoffParameters,
    add_pcb_standoff,
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
class BoardDisplayEnclosureBuild:
    """Resolved assembly, enclosure policy, specification, and parts."""

    assembly: DeviceAssembly
    specification: EnclosureSpecification
    enclosure_parameters: EnclosureParameters
    policy: BoardDisplayEnclosureParameters
    standoff_parameters: tuple[PcbStandoffParameters, ...]
    parts: dict[str, cq.Workplane]


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

    display_window_enabled: bool = True
    display_window_clearance_mm: float = 0.5

    board_standoffs_enabled: bool = True
    standoff_radial_wall_mm: float = 1.5
    standoff_hole_clearance_mm: float | None = None

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
            "standoff_radial_wall_mm": (self.standoff_radial_wall_mm),
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
            "display_window_clearance_mm": (self.display_window_clearance_mm),
            "corner_radius_mm": self.corner_radius_mm,
        }

        for name, value in non_negative_values.items():
            if value < 0:
                raise ValueError(f"{name} must not be negative")

        if (
            self.standoff_hole_clearance_mm is not None
            and self.standoff_hole_clearance_mm < 0
        ):
            raise ValueError("standoff_hole_clearance_mm must not be negative")

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


def _resolve_enclosure_build_inputs(
    design: BoardDisplayDesign,
    policy: BoardDisplayEnclosureParameters,
) -> tuple[
    DeviceAssembly,
    EnclosureSpecification,
    EnclosureParameters,
]:
    """Resolve the assembly, specification, and enclosure parameters."""
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

    enclosure_parameters = EnclosureParameters(
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

    return (
        assembly,
        specification,
        enclosure_parameters,
    )


def _build_enclosure_parameters(
    design: BoardDisplayDesign,
    policy: BoardDisplayEnclosureParameters,
) -> EnclosureParameters:
    """Resolve existing enclosure parameters from a design and policy."""
    _, _, enclosure_parameters = _resolve_enclosure_build_inputs(
        design,
        policy,
    )

    return enclosure_parameters


def _derive_board_standoff_parameters(
    *,
    assembly: DeviceAssembly,
    specification: EnclosureSpecification,
    enclosure_parameters: EnclosureParameters,
    policy: BoardDisplayEnclosureParameters,
) -> tuple[PcbStandoffParameters, ...]:
    """Derive enclosure-local standoffs from board assembly metadata."""
    if not policy.board_standoffs_enabled:
        return ()

    board = assembly.get("board")
    positions = assembly_mounting_hole_positions(board)

    if not positions:
        return ()

    mounting = board.metadata.get("mounting")

    if not isinstance(mounting, dict):
        raise TypeError("board mounting metadata must be a dictionary")

    hole_diameter_mm = mounting.get("hole_diameter_mm")
    recommended_clearance_mm = mounting.get("recommended_clearance_mm")

    if not isinstance(
        hole_diameter_mm,
        int | float,
    ):
        raise TypeError("board mounting hole diameter must be numeric")

    if not isinstance(
        recommended_clearance_mm,
        int | float,
    ):
        raise TypeError("board mounting clearance must be numeric")

    resolved_clearance_mm = (
        policy.standoff_hole_clearance_mm
        if policy.standoff_hole_clearance_mm is not None
        else recommended_clearance_mm
    )

    hole_with_clearance_mm = hole_diameter_mm + resolved_clearance_mm
    outer_diameter_mm = hole_with_clearance_mm + 2 * policy.standoff_radial_wall_mm

    body_bottom_z_mm = -enclosure_parameters.height / 2

    derived: list[PcbStandoffParameters] = []

    for world_x_mm, world_y_mm, board_bottom_z_mm in positions:
        standoff_height_mm = board_bottom_z_mm - specification.bottom_z_mm

        if standoff_height_mm <= 0:
            raise ValueError(
                "board mounting position must be above the enclosure cavity floor"
            )

        parameters = PcbStandoffParameters(
            x=(world_x_mm - specification.center_x_mm),
            y=(world_y_mm - specification.center_y_mm),
            base_height_mm=enclosure_parameters.floor,
            standoff_height_mm=standoff_height_mm,
            outer_diameter_mm=outer_diameter_mm,
            hole_diameter_mm=hole_with_clearance_mm,
            base_z_mm=body_bottom_z_mm,
        )
        parameters.validate()
        derived.append(parameters)

    return tuple(derived)


def _add_board_standoffs(
    *,
    body: cq.Workplane,
    parameters: tuple[PcbStandoffParameters, ...],
) -> cq.Workplane:
    """Add all derived PCB standoffs to an enclosure body."""
    result = body

    for standoff in parameters:
        result = add_pcb_standoff(
            result,
            parameters=standoff,
        )

    return result


def _build_display_window_cutter(
    *,
    assembly: DeviceAssembly,
    specification: EnclosureSpecification,
    enclosure_parameters: EnclosureParameters,
    policy: BoardDisplayEnclosureParameters,
) -> cq.Workplane:
    """Build the complete volume that must remain open above the display."""
    display = assembly.get("display")
    bounds = display.transformed_geometry().val().BoundingBox()

    window_width_mm = bounds.xlen + 2 * policy.display_window_clearance_mm
    window_depth_mm = bounds.ylen + 2 * policy.display_window_clearance_mm

    window_center_x_mm = (bounds.xmin + bounds.xmax) / 2 - specification.center_x_mm
    window_center_y_mm = (bounds.ymin + bounds.ymax) / 2 - specification.center_y_mm

    cutter_height_mm = (
        enclosure_parameters.lid_thickness + enclosure_parameters.lid_lip_height + 4.0
    )

    return (
        cq.Workplane("XY")
        .box(
            window_width_mm,
            window_depth_mm,
            cutter_height_mm,
        )
        .translate(
            (
                window_center_x_mm,
                window_center_y_mm,
                0.0,
            )
        )
    )


def _cut_display_window(
    *,
    lid: cq.Workplane,
    assembly: DeviceAssembly,
    specification: EnclosureSpecification,
    enclosure_parameters: EnclosureParameters,
    policy: BoardDisplayEnclosureParameters,
) -> cq.Workplane:
    """Cut a display opening through the enclosure lid."""
    if not policy.display_window_enabled:
        return lid

    cutter = _build_display_window_cutter(
        assembly=assembly,
        specification=specification,
        enclosure_parameters=enclosure_parameters,
        policy=policy,
    )

    return lid.cut(cutter)


def build_board_display_enclosure_result(
    design: BoardDisplayDesign,
    parameters: BoardDisplayEnclosureParameters | None = None,
) -> BoardDisplayEnclosureBuild:
    """Build and return all resolved enclosure-generation artifacts."""
    resolved = (
        parameters
        if parameters is not None
        else BoardDisplayEnclosureParameters(
            label=design.product,
        )
    )

    (
        assembly,
        specification,
        enclosure_parameters,
    ) = _resolve_enclosure_build_inputs(
        design,
        resolved,
    )

    standoff_parameters = _derive_board_standoff_parameters(
        assembly=assembly,
        specification=specification,
        enclosure_parameters=enclosure_parameters,
        policy=resolved,
    )

    parts = build_enclosure(enclosure_parameters)
    parts["body"] = _add_board_standoffs(
        body=parts["body"],
        parameters=standoff_parameters,
    )
    parts["lid"] = _cut_display_window(
        lid=parts["lid"],
        assembly=assembly,
        specification=specification,
        enclosure_parameters=enclosure_parameters,
        policy=resolved,
    )

    return BoardDisplayEnclosureBuild(
        assembly=assembly,
        specification=specification,
        enclosure_parameters=enclosure_parameters,
        policy=resolved,
        standoff_parameters=standoff_parameters,
        parts=parts,
    )


def build_board_display_enclosure(
    design: BoardDisplayDesign,
    parameters: BoardDisplayEnclosureParameters | None = None,
) -> dict[str, cq.Workplane]:
    """Build printable body and lid parts for a board-display design."""
    return build_board_display_enclosure_result(
        design,
        parameters,
    ).parts


def _analyze_board_standoff_fit(
    build: BoardDisplayEnclosureBuild,
    *,
    tolerance_mm: float = 1e-6,
) -> tuple[InterferenceFinding, ...]:
    """Verify generated standoffs against assembly mounting metadata."""
    board = build.assembly.get("board")
    world_positions = assembly_mounting_hole_positions(board)

    if not world_positions:
        return ()

    expected_positions = tuple(
        (
            world_x_mm - build.specification.center_x_mm,
            world_y_mm - build.specification.center_y_mm,
            world_z_mm,
        )
        for world_x_mm, world_y_mm, world_z_mm in world_positions
    )

    actual = build.standoff_parameters
    findings: list[InterferenceFinding] = []

    if len(actual) != len(expected_positions):
        findings.append(
            InterferenceFinding(
                first_identifier="board",
                second_identifier="standoffs",
                kind="mounting_count",
                required_clearance_mm=float(len(expected_positions)),
                measured_clearance_mm=float(len(actual)),
                clearance_source="assembly_mounting",
            )
        )

    mounting = board.metadata.get("mounting")

    if not isinstance(mounting, dict):
        raise TypeError("board mounting metadata must be a dictionary")

    hole_diameter_mm = mounting.get("hole_diameter_mm")
    recommended_clearance_mm = mounting.get("recommended_clearance_mm")

    if not isinstance(
        hole_diameter_mm,
        int | float,
    ):
        raise TypeError("board mounting hole diameter must be numeric")

    if not isinstance(
        recommended_clearance_mm,
        int | float,
    ):
        raise TypeError("board mounting clearance must be numeric")

    resolved_clearance_mm = (
        build.policy.standoff_hole_clearance_mm
        if (build.policy.standoff_hole_clearance_mm is not None)
        else recommended_clearance_mm
    )

    expected_hole_diameter_mm = hole_diameter_mm + resolved_clearance_mm
    expected_outer_diameter_mm = (
        expected_hole_diameter_mm + 2 * build.policy.standoff_radial_wall_mm
    )

    for index, (
        parameters,
        expected,
    ) in enumerate(
        zip(
            actual,
            expected_positions,
            strict=False,
        ),
        start=1,
    ):
        expected_x_mm, expected_y_mm, board_bottom_z_mm = expected
        identifier = f"standoff_{index}"

        center_offset_mm = hypot(
            parameters.x - expected_x_mm,
            parameters.y - expected_y_mm,
        )

        if center_offset_mm > tolerance_mm:
            findings.append(
                InterferenceFinding(
                    first_identifier="board",
                    second_identifier=identifier,
                    kind="mounting_alignment",
                    required_clearance_mm=tolerance_mm,
                    measured_clearance_mm=(center_offset_mm),
                    clearance_source=("assembly_mounting"),
                )
            )

        expected_height_mm = board_bottom_z_mm - build.specification.bottom_z_mm
        height_error_mm = abs(parameters.standoff_height_mm - expected_height_mm)

        if height_error_mm > tolerance_mm:
            findings.append(
                InterferenceFinding(
                    first_identifier="board",
                    second_identifier=identifier,
                    kind="mounting_height",
                    required_clearance_mm=tolerance_mm,
                    measured_clearance_mm=(height_error_mm),
                    clearance_source=("assembly_mounting"),
                )
            )

        hole_error_mm = abs(parameters.hole_diameter_mm - expected_hole_diameter_mm)

        if hole_error_mm > tolerance_mm:
            findings.append(
                InterferenceFinding(
                    first_identifier="board",
                    second_identifier=identifier,
                    kind="mounting_hole_diameter",
                    required_clearance_mm=(expected_hole_diameter_mm),
                    measured_clearance_mm=(parameters.hole_diameter_mm),
                    clearance_source=("assembly_mounting"),
                )
            )

        boss_error_mm = abs(parameters.outer_diameter_mm - expected_outer_diameter_mm)

        if boss_error_mm > tolerance_mm:
            findings.append(
                InterferenceFinding(
                    first_identifier="board",
                    second_identifier=identifier,
                    kind="mounting_boss_diameter",
                    required_clearance_mm=(expected_outer_diameter_mm),
                    measured_clearance_mm=(parameters.outer_diameter_mm),
                    clearance_source=("assembly_mounting"),
                )
            )

    return tuple(findings)


def analyze_board_display_enclosure_fit(
    build: BoardDisplayEnclosureBuild,
) -> InterferenceReport:
    """Analyze assembly fit against enclosure walls, floor, and lid."""
    parameters = build.enclosure_parameters
    specification = build.specification

    boundary = EnclosureBoundary(
        inner_width_mm=specification.inner_width_mm,
        inner_depth_mm=specification.inner_depth_mm,
        wall_height_mm=(parameters.height - parameters.floor),
        wall_thickness_mm=parameters.wall,
        center_x_mm=specification.center_x_mm,
        center_y_mm=specification.center_y_mm,
        bottom_z_mm=specification.bottom_z_mm,
    )

    findings: list[InterferenceFinding] = list(_analyze_board_standoff_fit(build))

    for component in build.assembly:
        for edge in (
            "negative_x",
            "positive_x",
            "negative_y",
            "positive_y",
        ):
            report = analyze_boundary_clearance(
                component=component,
                boundary=boundary,
                edge=edge,
                wall_identifier=f"{edge}_wall",
            )
            findings.extend(report.findings)

        bounds = component.transformed_geometry().val().BoundingBox()

        floor_z_mm = specification.bottom_z_mm
        lid_z_mm = specification.bottom_z_mm + specification.inner_height_mm

        if bounds.zmin < floor_z_mm - 1e-6:
            findings.append(
                InterferenceFinding(
                    first_identifier=component.identifier,
                    second_identifier="floor",
                    kind="collision",
                    intersection_volume_mm3=0.0,
                )
            )

        if bounds.zmax > lid_z_mm + 1e-6:
            findings.append(
                InterferenceFinding(
                    first_identifier=component.identifier,
                    second_identifier="lid",
                    kind="collision",
                    intersection_volume_mm3=0.0,
                )
            )

    required_window = _build_display_window_cutter(
        assembly=build.assembly,
        specification=build.specification,
        enclosure_parameters=build.enclosure_parameters,
        policy=build.policy,
    )
    lid = build.parts["lid"]

    obstructing_volume_mm3 = lid.intersect(required_window).val().Volume()

    if obstructing_volume_mm3 > 1e-6:
        findings.append(
            InterferenceFinding(
                first_identifier="display",
                second_identifier="display_window",
                kind="collision",
                intersection_volume_mm3=(obstructing_volume_mm3),
            )
        )

    return InterferenceReport(
        findings=tuple(findings),
    )
