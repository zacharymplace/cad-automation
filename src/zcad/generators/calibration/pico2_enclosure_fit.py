"""Refined two-part Raspberry Pi Pico 2 enclosure fit assembly."""

import math
from dataclasses import asdict, dataclass, replace
from functools import cached_property

import cadquery as cq
from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureBoundary,
    InterferenceReport,
    Placement,
    analyze_boundary_clearance,
    lowest_display_height_mm,
)
from zcad_core.features import (
    ConnectorCutoutParameters,
    DisplayBezelParameters,
    DisplayWindowParameters,
    add_board_standoffs,
    add_display_bezel,
    cut_connector_opening,
    cut_display_window,
)
from zcad_core.features.display_retainer import (
    DisplayRetainerParameters,
    add_display_retainer,
)
from zcad_core.features.labels import (
    add_embossed_label,
)
from zcad_core.hardware import (
    get_raspberry_pi_pico2,
    get_reference_oled_128x64,
)
from zcad_core.hardware.electronics import DisplaySpec

from zcad.assemblies import Pico2OledAssemblyParameters
from zcad.assemblies.board_display import (
    BoardDisplayProduct,
    analyze_board_display_product,
    build_board_display_product,
)
from zcad.assemblies.pico2_oled import PICO2_OLED_PRODUCT
from zcad.designs import parse_display_spec


@dataclass(frozen=True)
class UsbPlugEnvelope:
    """Measured or declared rectangular envelope of a plug's molded housing."""

    identifier: str
    width_mm: float
    height_mm: float
    housing_length_mm: float
    center_height_offset_mm: float
    clearance_mm: float
    nose_width_mm: float
    nose_height_mm: float
    nose_length_mm: float
    nose_center_height_offset_mm: float
    evidence_status: str
    evidence_source: str

    def __post_init__(self) -> None:
        for name in ("identifier", "evidence_source"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"usb_plug {name} must be a nonempty string")
        if self.evidence_status not in {"measured", "vendor_drawing", "test_envelope"}:
            raise ValueError(
                "usb_plug evidence_status must be measured, vendor_drawing, "
                "or test_envelope"
            )
        for name in (
            "width_mm",
            "height_mm",
            "housing_length_mm",
            "nose_width_mm",
            "nose_height_mm",
            "nose_length_mm",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValueError(
                    f"usb_plug {name} must be a finite number greater than zero"
                )
        for name in (
            "center_height_offset_mm",
            "clearance_mm",
            "nose_center_height_offset_mm",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"usb_plug {name} must be a finite number")
        if self.clearance_mm < 0:
            raise ValueError("usb_plug clearance_mm must not be negative")


@dataclass(frozen=True)
class Pico2EnclosureFitParameters:
    """Parameters for a Pico 2 enclosure and fitted lid."""

    display: DisplaySpec | dict[str, object] | None = None
    usb_plug: UsbPlugEnvelope | dict[str, object] | None = None

    usb_plug: UsbPlugEnvelope | dict[str, object] | None = None

    display_retention: str = "none"
    retention_clearance_mm: float = 0.3
    retention_wall_mm: float = 1.2
    retention_clip_reach_mm: float = 1.0
    retention_clip_lip_height_mm: float = 1.0
    retention_clip_gap_mm: float = 0.1

    wall_mm: float = 2.0
    floor_mm: float = 2.0
    internal_height_mm: float = 8.0
    board_clearance_mm: float = 2.0

    standoff_height_mm: float = 3.0
    standoff_radial_wall_mm: float = 1.5
    mounting_hole_clearance_mm: float = 0.5

    lid_thickness_mm: float = 2.0
    lid_clearance_mm: float = 0.25
    lid_lip_height_mm: float = 2.5
    lid_lip_wall_mm: float = 1.2

    corner_radius_mm: float = 3.0
    exterior_edge_fillet_mm: float = 0.6

    usb_width_clearance_mm: float = 0.6
    usb_height_clearance_mm: float = 0.6
    usb_access_clearance_mm: float = 2.0

    display_module_clearance_mm: float = 0.5
    display_window_clearance_mm: float = 0.4
    display_window_corner_radius_mm: float = 1.0
    display_bezel_wall_mm: float = 1.5
    display_bezel_height_mm: float = 0.8
    display_center_x_mm: float = 0.0
    display_center_y_mm: float = 6.0
    board_display_clearance_mm: float = 0.5

    label_text: str = "PICO 2 OLED"
    label_x_mm: float = 0.0
    label_y_mm: float = -18.0
    label_size_mm: float = 4.0
    label_height_mm: float = 0.5

    def __post_init__(self) -> None:
        """Freeze validated custom hardware, including JSON input."""
        if self.usb_plug is not None and not isinstance(self.usb_plug, UsbPlugEnvelope):
            if not isinstance(self.usb_plug, dict):
                raise ValueError("usb_plug must be an object")
            try:
                object.__setattr__(self, "usb_plug", UsbPlugEnvelope(**self.usb_plug))
            except TypeError as error:
                raise ValueError(f"invalid usb_plug fields: {error}") from None
        if self.usb_plug is not None and not isinstance(self.usb_plug, UsbPlugEnvelope):
            if not isinstance(self.usb_plug, dict):
                raise ValueError("usb_plug must be an object")
            try:
                object.__setattr__(self, "usb_plug", UsbPlugEnvelope(**self.usb_plug))
            except TypeError as error:
                raise ValueError(f"invalid usb_plug fields: {error}") from None
        if self.display is not None:
            document = (
                asdict(self.display)
                if isinstance(self.display, DisplaySpec)
                else self.display
            )
            object.__setattr__(self, "display", parse_display_spec(document))

    @property
    def display_spec(self) -> DisplaySpec:
        """Return selected hardware or the backwards-compatible reference."""
        return (
            self.display
            if isinstance(self.display, DisplaySpec)
            else get_reference_oled_128x64()
        )

    @cached_property
    def product(self) -> BoardDisplayProduct:
        """Retain the Pico board and its catalogued components."""
        return replace(PICO2_OLED_PRODUCT, display=self.display_spec)

    def validate(self) -> None:
        """Validate enclosure geometry."""
        if self.display_retention not in {"none", "clips"}:
            raise ValueError("display_retention must be 'none' or 'clips'")
        if self.display_retention == "clips" and self.display_spec.is_layered:
            raise ValueError(
                "clip retention requires a solid-envelope display; "
                "layered modules need PCB-specific support"
            )
        if self.usb_plug is not None:
            connector = get_raspberry_pi_pico2().usb_connector
            plug = self.usb_plug
            center_z = (
                self.device_assembly.get("usb_connector").placement.z_mm
                + connector.height_mm / 2
                + plug.center_height_offset_mm
            )
            if center_z - plug.height_mm / 2 - plug.clearance_mm < self.floor_mm:
                raise ValueError("usb_plug envelope cuts into the enclosure floor")
            if center_z + plug.height_mm / 2 + plug.clearance_mm >= self.body_height_mm:
                raise ValueError("usb_plug envelope reaches above the enclosure wall")

        positive_values = {
            "retention_wall_mm": self.retention_wall_mm,
            "retention_clip_reach_mm": self.retention_clip_reach_mm,
            "retention_clip_lip_height_mm": self.retention_clip_lip_height_mm,
            "wall_mm": self.wall_mm,
            "floor_mm": self.floor_mm,
            "internal_height_mm": self.internal_height_mm,
            "board_clearance_mm": self.board_clearance_mm,
            "standoff_height_mm": self.standoff_height_mm,
            "standoff_radial_wall_mm": (self.standoff_radial_wall_mm),
            "lid_thickness_mm": self.lid_thickness_mm,
            "lid_lip_height_mm": self.lid_lip_height_mm,
            "lid_lip_wall_mm": self.lid_lip_wall_mm,
            "display_module_clearance_mm": (self.display_module_clearance_mm),
            "display_bezel_wall_mm": (self.display_bezel_wall_mm),
            "display_bezel_height_mm": (self.display_bezel_height_mm),
            "label_size_mm": self.label_size_mm,
            "label_height_mm": self.label_height_mm,
        }

        for name, value in positive_values.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"{name} must be a finite number")
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        nonnegative_values = {
            "retention_clearance_mm": self.retention_clearance_mm,
            "retention_clip_gap_mm": self.retention_clip_gap_mm,
            "mounting_hole_clearance_mm": (self.mounting_hole_clearance_mm),
            "lid_clearance_mm": self.lid_clearance_mm,
            "corner_radius_mm": self.corner_radius_mm,
            "exterior_edge_fillet_mm": (self.exterior_edge_fillet_mm),
            "usb_width_clearance_mm": (self.usb_width_clearance_mm),
            "usb_height_clearance_mm": (self.usb_height_clearance_mm),
            "usb_access_clearance_mm": (self.usb_access_clearance_mm),
            "display_window_clearance_mm": (self.display_window_clearance_mm),
            "display_window_corner_radius_mm": (self.display_window_corner_radius_mm),
            "board_display_clearance_mm": self.board_display_clearance_mm,
        }

        for name, value in nonnegative_values.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"{name} must be a finite number")
            if value < 0:
                raise ValueError(f"{name} must not be negative")

        if self.usb_plug is not None:
            connector = get_raspberry_pi_pico2().usb_connector
            component = self.device_assembly.get("usb_connector")
            plug_bottom = (
                component.placement.z_mm
                + connector.height_mm / 2
                + self.usb_plug.nose_center_height_offset_mm
                - self.usb_plug.nose_height_mm / 2
                - self.usb_plug.clearance_mm
            )
            port_face_y = component.transformed_geometry().val().BoundingBox().ymin
            required_insertion = port_face_y + self.outer_depth_mm / 2
            if self.usb_plug.nose_length_mm < required_insertion:
                raise ValueError("usb_plug nose is too short to reach the receptacle")
            if plug_bottom < self.floor_mm:
                raise ValueError("usb_plug envelope cuts into the enclosure floor")
            if (
                component.placement.z_mm
                + connector.height_mm / 2
                + self.usb_plug.nose_center_height_offset_mm
                + self.usb_plug.nose_height_mm / 2
                + self.usb_plug.clearance_mm
                >= self.body_height_mm
            ):
                raise ValueError("usb_plug envelope reaches above the enclosure wall")
        if self.display_retention == "clips":
            self.retention_parameters.validate()

        if self.corner_radius_mm >= (
            min(
                self.outer_width_mm,
                self.outer_depth_mm,
            )
            / 2
        ):
            raise ValueError("corner_radius_mm is too large")

        if self.exterior_edge_fillet_mm >= (self.wall_mm):
            raise ValueError("exterior_edge_fillet_mm must be smaller than wall_mm")

        display = self.display_spec

        window_width_mm = display.active_width_mm + (
            2 * self.display_window_clearance_mm
        )
        window_height_mm = display.active_height_mm + (
            2 * self.display_window_clearance_mm
        )

        bezel_width_mm = window_width_mm + (2 * self.display_bezel_wall_mm)
        bezel_height_mm = window_height_mm + (2 * self.display_bezel_wall_mm)

        display_component = self.device_assembly.get("display")

        if abs(display_component.placement.x_mm + display.active_center_x_mm) + (
            bezel_width_mm / 2
        ) > (self.outer_width_mm / 2):
            raise ValueError("display bezel does not fit within lid width")

        if abs(display_component.placement.y_mm + display.active_center_y_mm) + (
            bezel_height_mm / 2
        ) > (self.outer_depth_mm / 2):
            raise ValueError("display bezel does not fit within lid depth")

        if not self.label_text.strip():
            raise ValueError("label_text must not be empty")

        report = analyze_board_display_product(
            self.product,
            self.device_assembly,
            minimum_board_display_clearance_mm=(self.board_display_clearance_mm),
        )

        if report.collisions:
            finding = report.collisions[0]

            raise ValueError(
                "Pico 2 OLED enclosure assembly collision: "
                f"{finding.first_identifier} and "
                f"{finding.second_identifier}"
            )

        if report.clearance_violations:
            finding = report.clearance_violations[0]

            raise ValueError(
                "Pico 2 OLED enclosure assembly clearance "
                "is insufficient: "
                f"{finding.measured_clearance_mm:.3f} mm measured, "
                f"{finding.required_clearance_mm:.3f} mm required"
            )

        access_report = _analyze_usb_access_clearance(self)

        if access_report.has_findings:
            finding = access_report.findings[0]

            raise ValueError(
                "Pico 2 USB access clearance is insufficient: "
                f"{finding.measured_clearance_mm:.3f} mm measured, "
                f"{finding.required_clearance_mm:.3f} mm required"
            )

    @cached_property
    def assembly_parameters(
        self,
    ) -> Pico2OledAssemblyParameters:
        """Return authoritative policy-compliant placements."""
        board = get_raspberry_pi_pico2()
        display = self.display_spec

        board_z_mm = self.floor_mm + self.standoff_height_mm
        nominal_display_z_mm = (
            self.floor_mm + self.internal_height_mm - display.module_depth_mm
        )
        # Bound the complete retainer footprint below the module while solving
        # component clearance. This conservative box includes the clip lips.
        drop_mm = 0.0
        solver_display = display
        if self.display_retention == "clips":
            drop_mm = self.retention_clip_gap_mm + self.retention_clip_lip_height_mm
            outside_mm = self.retention_clearance_mm + self.retention_wall_mm
            solver_display = replace(
                display,
                module_width_mm=display.module_width_mm + 2 * outside_mm,
                module_height_mm=display.module_height_mm + 2 * outside_mm,
                module_depth_mm=display.module_depth_mm + drop_mm,
            )
        display_z_mm = (
            lowest_display_height_mm(
                board=board,
                display=solver_display,
                board_placement=Placement(z_mm=board_z_mm),
                display_placement=Placement(
                    x_mm=self.display_center_x_mm,
                    y_mm=self.display_center_y_mm,
                ),
                board_display_clearance_mm=self.board_display_clearance_mm,
                connector_access_clearance_mm=self.usb_access_clearance_mm,
                minimum_mm=nominal_display_z_mm - drop_mm,
            )
            + drop_mm
        )

        return Pico2OledAssemblyParameters(
            board_x_mm=0.0,
            board_y_mm=0.0,
            board_z_mm=board_z_mm,
            display_x_mm=self.display_center_x_mm,
            display_y_mm=self.display_center_y_mm,
            display_z_mm=display_z_mm,
            board_display_clearance_mm=(self.board_display_clearance_mm),
            usb_access_clearance_mm=(self.usb_access_clearance_mm),
        )

    @cached_property
    def device_assembly(self) -> DeviceAssembly:
        """Return the placed Pico 2 and OLED assembly."""
        return build_board_display_product(
            self.product, parameters=self.assembly_parameters
        )

    @cached_property
    def retention_parameters(self) -> DisplayRetainerParameters:
        """Core retainer in seated assembly coordinates."""
        component = self.device_assembly.get("display")
        return DisplayRetainerParameters(
            center_x_mm=component.placement.x_mm,
            center_y_mm=component.placement.y_mm,
            module_width_mm=self.display_spec.module_width_mm,
            module_depth_mm=self.display_spec.module_height_mm,
            module_thickness_mm=self.display_spec.module_depth_mm,
            module_top_z_mm=component.placement.z_mm
            + self.display_spec.module_depth_mm,
            lid_underside_z_mm=self.body_height_mm,
            clearance_mm=self.retention_clearance_mm,
            wall_mm=self.retention_wall_mm,
            clip_reach_mm=self.retention_clip_reach_mm,
            clip_lip_height_mm=self.retention_clip_lip_height_mm,
            clip_gap_mm=self.retention_clip_gap_mm,
        )

    @property
    def display_side_allowance_mm(self) -> float:
        existing = (
            self.display_module_clearance_mm
            + self.lid_clearance_mm
            + self.lid_lip_wall_mm
        )
        if self.display_retention == "clips":
            return max(
                existing,
                self.retention_clearance_mm
                + self.retention_wall_mm
                + self.display_module_clearance_mm,
            )
        return existing

    def _required_component_span_mm(
        self,
        *,
        identifier: str,
        axis: str,
        clearance_mm: float,
    ) -> float:
        """Return centered span required by one component."""
        component = self.device_assembly.get(identifier)

        if axis == "x":
            center_mm = component.placement.x_mm
            dimension_mm = float(component.metadata["width_mm"])
        elif axis == "y":
            center_mm = component.placement.y_mm
            dimension_mm = float(component.metadata["depth_mm"])
        else:
            raise ValueError(f"Unsupported assembly axis: {axis}")

        return 2 * (abs(center_mm) + (dimension_mm / 2) + clearance_mm)

    @property
    def inner_width_mm(self) -> float:
        """Return assembly-derived enclosure cavity width."""
        board_required_width_mm = self._required_component_span_mm(
            identifier="board",
            axis="x",
            clearance_mm=self.board_clearance_mm,
        )

        display_required_width_mm = self._required_component_span_mm(
            identifier="display",
            axis="x",
            clearance_mm=self.display_side_allowance_mm,
        )

        return max(
            board_required_width_mm,
            display_required_width_mm,
        )

    @property
    def inner_depth_mm(self) -> float:
        """Return assembly-derived enclosure cavity depth."""
        board_required_depth_mm = self._required_component_span_mm(
            identifier="board",
            axis="y",
            clearance_mm=self.board_clearance_mm,
        )

        display_required_depth_mm = self._required_component_span_mm(
            identifier="display",
            axis="y",
            clearance_mm=self.display_side_allowance_mm,
        )

        connector_required_depth_mm = self._required_component_span_mm(
            identifier="usb_connector",
            axis="y",
            clearance_mm=(self.usb_access_clearance_mm),
        )

        return max(
            board_required_depth_mm,
            display_required_depth_mm,
            connector_required_depth_mm,
        )

    @property
    def outer_width_mm(self) -> float:
        """Return enclosure exterior width."""
        return self.inner_width_mm + (2 * self.wall_mm)

    @property
    def outer_depth_mm(self) -> float:
        """Return enclosure exterior depth."""
        return self.inner_depth_mm + (2 * self.wall_mm)

    @property
    def body_height_mm(self) -> float:
        """Keep the requested cavity as a minimum and contain the raised display."""
        display = self.device_assembly.get("display")
        return max(
            self.floor_mm + self.internal_height_mm,
            display.placement.z_mm + float(display.metadata["height_mm"]),
        )

    @property
    def lid_height_mm(self) -> float:
        """Return structural lid height including the locating lip."""
        return self.lid_lip_height_mm + self.lid_thickness_mm

    @property
    def lid_overall_height_mm(self) -> float:
        """Return total lid height including the raised display bezel."""
        lowest_mm = 0.0
        if self.display_retention == "clips":
            lowest_mm = min(
                0.0,
                self.lid_lip_height_mm
                - self.display_spec.module_depth_mm
                - self.retention_clip_gap_mm
                - self.retention_clip_lip_height_mm,
            )
        return self.lid_height_mm + self.display_bezel_height_mm - lowest_mm


def _fillet_vertical_edges(
    model: cq.Workplane,
    *,
    radius_mm: float,
) -> cq.Workplane:
    """Fillet vertical exterior edges when requested."""
    if radius_mm <= 0:
        return model

    return model.edges("|Z").fillet(radius_mm)


def _enclosure_boundary(
    parameters: Pico2EnclosureFitParameters,
) -> EnclosureBoundary:
    """Return the reusable enclosure cavity boundary."""
    return EnclosureBoundary(
        inner_width_mm=parameters.inner_width_mm,
        inner_depth_mm=parameters.inner_depth_mm,
        wall_height_mm=parameters.body_height_mm,
        wall_thickness_mm=parameters.wall_mm,
    )


def _analyze_usb_access_clearance(
    parameters: Pico2EnclosureFitParameters,
) -> InterferenceReport:
    """Validate USB access clearance against the enclosure wall."""
    return analyze_boundary_clearance(
        component=parameters.device_assembly.get("usb_connector"),
        boundary=_enclosure_boundary(parameters),
        edge="negative_y",
    )


def _connector_cutout_parameters(
    parameters: Pico2EnclosureFitParameters,
) -> ConnectorCutoutParameters:
    """Derive the USB opening through the reusable core API."""
    board = get_raspberry_pi_pico2()

    connector_component = parameters.device_assembly.get("usb_connector")
    width_clearance = parameters.usb_width_clearance_mm
    height_clearance = parameters.usb_height_clearance_mm
    bottom_z = connector_component.placement.z_mm
    if parameters.usb_plug is not None:
        plug = parameters.usb_plug
        if board.usb_connector.board_edge != "negative_y":
            raise ValueError(
                "USB plug insertion currently supports the Pico negative-Y port"
            )
        width_clearance = max(
            width_clearance,
            plug.nose_width_mm + 2 * plug.clearance_mm - board.usb_connector.width_mm,
        )
        opening_height = max(
            board.usb_connector.height_mm + height_clearance,
            plug.nose_height_mm + 2 * plug.clearance_mm,
        )
        height_clearance = opening_height - board.usb_connector.height_mm
        bottom_z = (
            connector_component.placement.z_mm
            + (board.usb_connector.height_mm - opening_height) / 2
            + plug.nose_center_height_offset_mm
        )
    cutout = ConnectorCutoutParameters.from_component(
        component=connector_component,
        connector=board.usb_connector,
        width_clearance_mm=width_clearance,
        height_clearance_mm=height_clearance,
        cutter_depth_mm=parameters.wall_mm + 2.0,
    )
    return replace(cutout, bottom_z_mm=bottom_z)


def _build_body(
    parameters: Pico2EnclosureFitParameters,
) -> cq.Workplane:
    """Build the refined open enclosure body."""
    board = get_raspberry_pi_pico2()

    body = cq.Workplane("XY").box(
        parameters.outer_width_mm,
        parameters.outer_depth_mm,
        parameters.body_height_mm,
        centered=(True, True, False),
    )

    body = _fillet_vertical_edges(
        body,
        radius_mm=parameters.corner_radius_mm,
    )

    cavity = (
        cq.Workplane("XY")
        .workplane(
            offset=parameters.floor_mm,
        )
        .box(
            parameters.inner_width_mm,
            parameters.inner_depth_mm,
            parameters.body_height_mm - parameters.floor_mm + 0.5,
            centered=(True, True, False),
        )
    )

    body = body.cut(cavity)

    body = add_board_standoffs(
        body,
        board=board,
        base_height_mm=parameters.floor_mm,
        standoff_height_mm=(parameters.standoff_height_mm),
        radial_wall_mm=(parameters.standoff_radial_wall_mm),
        hole_clearance_mm=(parameters.mounting_hole_clearance_mm),
    )

    cutout_parameters = _connector_cutout_parameters(parameters)

    body = cut_connector_opening(
        body,
        parameters=cutout_parameters,
    )

    if parameters.exterior_edge_fillet_mm > 0:
        body = body.edges("<Z").fillet(parameters.exterior_edge_fillet_mm)

    return body


def _build_lid(
    parameters: Pico2EnclosureFitParameters,
) -> cq.Workplane:
    """Build a refined fitted and labeled lid."""
    lip_outer_width_mm = parameters.inner_width_mm - (2 * parameters.lid_clearance_mm)
    lip_outer_depth_mm = parameters.inner_depth_mm - (2 * parameters.lid_clearance_mm)

    lip_inner_width_mm = lip_outer_width_mm - (2 * parameters.lid_lip_wall_mm)
    lip_inner_depth_mm = lip_outer_depth_mm - (2 * parameters.lid_lip_wall_mm)

    if lip_inner_width_mm <= 0:
        raise ValueError("lid lip leaves no internal width")

    if lip_inner_depth_mm <= 0:
        raise ValueError("lid lip leaves no internal depth")

    lip_outer = cq.Workplane("XY").box(
        lip_outer_width_mm,
        lip_outer_depth_mm,
        parameters.lid_lip_height_mm,
        centered=(True, True, False),
    )

    lip_inner = cq.Workplane("XY").box(
        lip_inner_width_mm,
        lip_inner_depth_mm,
        parameters.lid_lip_height_mm + 0.5,
        centered=(True, True, False),
    )

    lip_ring = lip_outer.cut(lip_inner)

    lid_plate = (
        cq.Workplane("XY")
        .workplane(
            offset=parameters.lid_lip_height_mm,
        )
        .box(
            parameters.outer_width_mm,
            parameters.outer_depth_mm,
            parameters.lid_thickness_mm,
            centered=(True, True, False),
        )
    )

    lid_plate = _fillet_vertical_edges(
        lid_plate,
        radius_mm=parameters.corner_radius_mm,
    )

    lid = lid_plate.union(lip_ring)

    if parameters.exterior_edge_fillet_mm > 0:
        lid = lid.edges(">Z").fillet(parameters.exterior_edge_fillet_mm)

    display = parameters.display_spec
    display_component = parameters.device_assembly.get("display")

    window = DisplayWindowParameters.from_display(
        display=display,
        panel_base_z_mm=(parameters.lid_lip_height_mm),
        panel_thickness_mm=(parameters.lid_thickness_mm),
        x=display_component.placement.x_mm,
        y=display_component.placement.y_mm,
        window_clearance_mm=(parameters.display_window_clearance_mm),
        corner_radius_mm=(parameters.display_window_corner_radius_mm),
    )

    lid = cut_display_window(
        lid,
        parameters=window,
    )

    bezel = DisplayBezelParameters.from_window(
        window=window,
        bezel_wall_mm=(parameters.display_bezel_wall_mm),
        bezel_height_mm=(parameters.display_bezel_height_mm),
    )

    lid = add_display_bezel(
        lid,
        parameters=bezel,
    )

    if parameters.display_retention == "clips":
        retainer = parameters.retention_parameters
        seated_z_mm = parameters.body_height_mm - parameters.lid_lip_height_mm
        lid = add_display_retainer(
            lid,
            parameters=replace(
                retainer,
                module_top_z_mm=retainer.module_top_z_mm - seated_z_mm,
                lid_underside_z_mm=retainer.lid_underside_z_mm - seated_z_mm,
            ),
        )

    label_base_z_mm = parameters.lid_lip_height_mm + parameters.lid_thickness_mm

    return add_embossed_label(
        lid,
        text=parameters.label_text,
        x=parameters.label_x_mm,
        y=parameters.label_y_mm,
        base_height=label_base_z_mm,
        text_size=parameters.label_size_mm,
        emboss_height=parameters.label_height_mm,
    )


def build_pico2_enclosure_fit(
    parameters: Pico2EnclosureFitParameters,
) -> dict[str, cq.Workplane]:
    """Build the refined Pico 2 body and lid."""
    parameters.validate()

    parts = {"body": _build_body(parameters), "lid": _build_lid(parameters)}
    if parameters.display_retention == "clips":
        seated = parts["lid"].translate(
            (0, 0, parameters.body_height_mm - parameters.lid_lip_height_mm)
        )
        for component in parameters.device_assembly:
            overlap = seated.intersect(component.transformed_geometry()).val().Volume()
            if overlap > 1e-6:
                raise ValueError(
                    f"OLED retainer intersects {component.identifier}: "
                    f"{overlap:.6f} mm3"
                )
        if seated.intersect(parts["body"]).val().Volume() > 1e-6:
            raise ValueError("OLED retainer intersects enclosure body")
    return parts
