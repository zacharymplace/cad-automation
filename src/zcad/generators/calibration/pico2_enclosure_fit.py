"""Refined two-part Raspberry Pi Pico 2 enclosure fit assembly."""

from dataclasses import dataclass

import cadquery as cq
from zcad_core.features import (
    ConnectorCutoutParameters,
    DisplayBezelParameters,
    DisplayWindowParameters,
    add_board_standoffs,
    add_display_bezel,
    cut_connector_opening,
    cut_display_window,
)
from zcad_core.features.labels import (
    add_embossed_label,
)
from zcad_core.hardware import (
    get_raspberry_pi_pico2,
    get_reference_oled_128x64,
)

from zcad.assemblies import (
    Pico2OledAssemblyParameters,
    analyze_pico2_oled_assembly,
    build_pico2_oled_assembly,
)


@dataclass(frozen=True)
class Pico2EnclosureFitParameters:
    """Parameters for a Pico 2 enclosure and fitted lid."""

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

    def validate(self) -> None:
        """Validate enclosure geometry."""
        positive_values = {
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
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        nonnegative_values = {
            "mounting_hole_clearance_mm": (self.mounting_hole_clearance_mm),
            "lid_clearance_mm": self.lid_clearance_mm,
            "corner_radius_mm": self.corner_radius_mm,
            "exterior_edge_fillet_mm": (self.exterior_edge_fillet_mm),
            "usb_width_clearance_mm": (self.usb_width_clearance_mm),
            "usb_height_clearance_mm": (self.usb_height_clearance_mm),
            "display_window_clearance_mm": (self.display_window_clearance_mm),
            "display_window_corner_radius_mm": (self.display_window_corner_radius_mm),
            "board_display_clearance_mm": self.board_display_clearance_mm,
        }

        for name, value in nonnegative_values.items():
            if value < 0:
                raise ValueError(f"{name} must not be negative")

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

        display = get_reference_oled_128x64()

        window_width_mm = display.active_width_mm + (
            2 * self.display_window_clearance_mm
        )
        window_height_mm = display.active_height_mm + (
            2 * self.display_window_clearance_mm
        )

        bezel_width_mm = window_width_mm + (2 * self.display_bezel_wall_mm)
        bezel_height_mm = window_height_mm + (2 * self.display_bezel_wall_mm)

        display_component = self.device_assembly.get("display")

        if abs(display_component.placement.x_mm) + (bezel_width_mm / 2) > (
            self.outer_width_mm / 2
        ):
            raise ValueError("display bezel does not fit within lid width")

        if abs(display_component.placement.y_mm) + (bezel_height_mm / 2) > (
            self.outer_depth_mm / 2
        ):
            raise ValueError("display bezel does not fit within lid depth")

        if not self.label_text.strip():
            raise ValueError("label_text must not be empty")

        report = analyze_pico2_oled_assembly(
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

    @property
    def assembly_parameters(
        self,
    ) -> Pico2OledAssemblyParameters:
        """Return authoritative policy-compliant placements."""
        board = get_raspberry_pi_pico2()
        display = get_reference_oled_128x64()

        board_z_mm = self.floor_mm + self.standoff_height_mm
        board_top_z_mm = board_z_mm + board.board_thickness_mm

        nominal_display_z_mm = self.body_height_mm - display.module_depth_mm
        minimum_display_z_mm = board_top_z_mm + self.board_display_clearance_mm

        return Pico2OledAssemblyParameters(
            board_x_mm=0.0,
            board_y_mm=0.0,
            board_z_mm=board_z_mm,
            display_x_mm=self.display_center_x_mm,
            display_y_mm=self.display_center_y_mm,
            display_z_mm=max(
                nominal_display_z_mm,
                minimum_display_z_mm,
            ),
            board_display_clearance_mm=(self.board_display_clearance_mm),
        )

    @property
    def device_assembly(self):
        """Return the placed Pico 2 and OLED assembly."""
        return build_pico2_oled_assembly(self.assembly_parameters)

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
            clearance_mm=(
                self.display_module_clearance_mm
                + self.lid_clearance_mm
                + self.lid_lip_wall_mm
            ),
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
            clearance_mm=(
                self.display_module_clearance_mm
                + self.lid_clearance_mm
                + self.lid_lip_wall_mm
            ),
        )

        return max(
            board_required_depth_mm,
            display_required_depth_mm,
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
        """Return enclosure body height."""
        return self.floor_mm + self.internal_height_mm

    @property
    def lid_height_mm(self) -> float:
        """Return structural lid height including the locating lip."""
        return self.lid_lip_height_mm + self.lid_thickness_mm

    @property
    def lid_overall_height_mm(self) -> float:
        """Return total lid height including the raised display bezel."""
        return self.lid_height_mm + self.display_bezel_height_mm


def _fillet_vertical_edges(
    model: cq.Workplane,
    *,
    radius_mm: float,
) -> cq.Workplane:
    """Fillet vertical exterior edges when requested."""
    if radius_mm <= 0:
        return model

    return model.edges("|Z").fillet(radius_mm)


def _build_body(
    parameters: Pico2EnclosureFitParameters,
) -> cq.Workplane:
    """Build the refined open enclosure body."""
    board = get_raspberry_pi_pico2()
    board_component = parameters.device_assembly.get("board")

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
            parameters.internal_height_mm + 0.5,
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

    board_top_z_mm = board_component.placement.z_mm + board.board_thickness_mm

    cutout_parameters = ConnectorCutoutParameters.from_connector(
        connector=board.usb_connector,
        board_top_z_mm=board_top_z_mm,
        width_clearance_mm=(parameters.usb_width_clearance_mm),
        height_clearance_mm=(parameters.usb_height_clearance_mm),
        cutter_depth_mm=(parameters.wall_mm + 2.0),
    )

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

    display = get_reference_oled_128x64()
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

    return {
        "body": _build_body(parameters),
        "lid": _build_lid(parameters),
    }
