"""Reusable Raspberry Pi Pico 2 and OLED device assembly."""

from dataclasses import dataclass

from zcad_core.assemblies import (
    ClearanceEnvelope,
    ClearancePolicy,
    DeviceAssembly,
    InterferenceReport,
    Placement,
    build_board_edge_connector_component,
    build_rectangular_hardware_component,
    component_pair,
)
from zcad_core.hardware import (
    get_raspberry_pi_pico2,
    get_reference_oled_128x64,
)


@dataclass(frozen=True)
class Pico2OledAssemblyParameters:
    """Authoritative placements for a Pico 2 and OLED assembly."""

    board_x_mm: float = 0.0
    board_y_mm: float = 0.0
    board_z_mm: float = 3.0

    display_x_mm: float = 0.0
    display_y_mm: float = 6.0
    display_z_mm: float = 8.0

    board_display_clearance_mm: float = 0.5
    usb_access_clearance_mm: float = 2.0

    def validate(self) -> None:
        """Validate component elevations."""
        if self.board_z_mm < 0:
            raise ValueError("board_z_mm must not be negative")

        if self.display_z_mm < 0:
            raise ValueError("display_z_mm must not be negative")

        if self.board_display_clearance_mm < 0:
            raise ValueError("board_display_clearance_mm must not be negative")

        if self.usb_access_clearance_mm < 0:
            raise ValueError("usb_access_clearance_mm must not be negative")


def build_pico2_oled_assembly(
    parameters: Pico2OledAssemblyParameters | None = None,
) -> DeviceAssembly:
    """Build the reusable Pico 2, USB, and OLED device assembly."""
    resolved = parameters if parameters is not None else Pico2OledAssemblyParameters()

    resolved.validate()

    board = get_raspberry_pi_pico2()
    display = get_reference_oled_128x64()
    connector = board.usb_connector

    return DeviceAssembly(
        (
            build_rectangular_hardware_component(
                identifier="board",
                hardware_identifier=board.identifier,
                kind="pcb",
                width_mm=board.board_width_mm,
                depth_mm=board.board_length_mm,
                height_mm=board.board_thickness_mm,
                placement=Placement(
                    x_mm=resolved.board_x_mm,
                    y_mm=resolved.board_y_mm,
                    z_mm=resolved.board_z_mm,
                ),
                clearance_envelope=ClearanceEnvelope(
                    positive_z_mm=resolved.board_display_clearance_mm,
                ),
            ),
            build_board_edge_connector_component(
                identifier="usb_connector",
                connector=connector,
                board_width_mm=board.board_width_mm,
                board_length_mm=board.board_length_mm,
                board_thickness_mm=board.board_thickness_mm,
                board_placement=Placement(
                    x_mm=resolved.board_x_mm,
                    y_mm=resolved.board_y_mm,
                    z_mm=resolved.board_z_mm,
                ),
                clearance_envelope=ClearanceEnvelope.for_edge(
                    edge=connector.board_edge,
                    clearance_mm=resolved.usb_access_clearance_mm,
                ),
            ),
            build_rectangular_hardware_component(
                identifier="display",
                hardware_identifier=display.identifier,
                kind="display",
                width_mm=display.module_width_mm,
                depth_mm=display.module_height_mm,
                height_mm=display.module_depth_mm,
                placement=Placement(
                    x_mm=resolved.display_x_mm,
                    y_mm=resolved.display_y_mm,
                    z_mm=resolved.display_z_mm,
                ),
                metadata={
                    "mount_style": display.mount_style,
                },
            ),
        )
    )


def analyze_pico2_oled_assembly(
    assembly: DeviceAssembly,
    *,
    minimum_board_display_clearance_mm: float = 0.5,
) -> InterferenceReport:
    """Analyze attachment and board-to-display policies."""
    if minimum_board_display_clearance_mm < 0:
        raise ValueError("minimum_board_display_clearance_mm must not be negative")

    expected_identifiers = {
        "board",
        "usb_connector",
        "display",
    }
    actual_identifiers = set(assembly.identifiers)

    if actual_identifiers != expected_identifiers:
        raise ValueError(
            "Pico 2 OLED assembly must contain exactly "
            "board, usb_connector, and display components"
        )

    return assembly.analyze_interference(
        allowed_contact_pairs=(
            component_pair(
                "board",
                "usb_connector",
            ),
        ),
        clearance_policy=ClearancePolicy(
            component_envelopes={
                "board": ClearanceEnvelope(
                    positive_z_mm=(minimum_board_display_clearance_mm),
                ),
            }
        ),
    )
