"""Reusable Raspberry Pi Pico 2 and OLED device assembly."""

from dataclasses import dataclass

import cadquery as cq
from zcad_core.assemblies import (
    AssemblyComponent,
    ClearanceEnvelope,
    ClearancePolicy,
    DeviceAssembly,
    InterferenceReport,
    Placement,
    component_pair,
)
from zcad_core.hardware import (
    RectangularConnectorSpec,
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


def _build_board_proxy() -> cq.Workplane:
    """Build a mechanical proxy from the Pico 2 specification."""
    board = get_raspberry_pi_pico2()

    return cq.Workplane("XY").box(
        board.board_width_mm,
        board.board_length_mm,
        board.board_thickness_mm,
        centered=(True, True, False),
    )


def _build_display_proxy() -> cq.Workplane:
    """Build a mechanical proxy from the display specification."""
    display = get_reference_oled_128x64()

    return cq.Workplane("XY").box(
        display.module_width_mm,
        display.module_height_mm,
        display.module_depth_mm,
        centered=(True, True, False),
    )


def _build_connector_proxy(
    connector: RectangularConnectorSpec,
) -> cq.Workplane:
    """Build a connector-body proxy from catalog metadata."""
    connector.validate()

    if connector.board_edge in {
        "negative_y",
        "positive_y",
    }:
        size_x_mm = connector.width_mm
        size_y_mm = connector.depth_mm
    else:
        size_x_mm = connector.depth_mm
        size_y_mm = connector.width_mm

    return cq.Workplane("XY").box(
        size_x_mm,
        size_y_mm,
        connector.height_mm,
        centered=(True, True, False),
    )


def _connector_placement(
    *,
    parameters: Pico2OledAssemblyParameters,
    connector: RectangularConnectorSpec,
) -> Placement:
    """Return connector placement relative to the placed board."""
    board = get_raspberry_pi_pico2()

    if connector.board_edge == "negative_y":
        connector_x_mm = parameters.board_x_mm + connector.center_offset_mm
        connector_y_mm = (
            parameters.board_y_mm
            - (board.board_length_mm / 2)
            + (connector.depth_mm / 2)
        )
    elif connector.board_edge == "positive_y":
        connector_x_mm = parameters.board_x_mm + connector.center_offset_mm
        connector_y_mm = (
            parameters.board_y_mm
            + (board.board_length_mm / 2)
            - (connector.depth_mm / 2)
        )
    elif connector.board_edge == "negative_x":
        connector_x_mm = (
            parameters.board_x_mm
            - (board.board_width_mm / 2)
            + (connector.depth_mm / 2)
        )
        connector_y_mm = parameters.board_y_mm + connector.center_offset_mm
    else:
        connector_x_mm = (
            parameters.board_x_mm
            + (board.board_width_mm / 2)
            - (connector.depth_mm / 2)
        )
        connector_y_mm = parameters.board_y_mm + connector.center_offset_mm

    connector_z_mm = (
        parameters.board_z_mm
        + board.board_thickness_mm
        + connector.bottom_offset_from_board_top_mm
    )

    return Placement(
        x_mm=connector_x_mm,
        y_mm=connector_y_mm,
        z_mm=connector_z_mm,
    )


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
            AssemblyComponent(
                identifier="board",
                geometry=_build_board_proxy(),
                placement=Placement(
                    x_mm=resolved.board_x_mm,
                    y_mm=resolved.board_y_mm,
                    z_mm=resolved.board_z_mm,
                ),
                metadata={
                    "kind": "pcb",
                    "hardware_identifier": board.identifier,
                    "width_mm": board.board_width_mm,
                    "depth_mm": board.board_length_mm,
                    "height_mm": board.board_thickness_mm,
                },
                clearance_envelope=ClearanceEnvelope(
                    positive_z_mm=(resolved.board_display_clearance_mm),
                ),
            ),
            AssemblyComponent(
                identifier="usb_connector",
                geometry=_build_connector_proxy(connector),
                placement=_connector_placement(
                    parameters=resolved,
                    connector=connector,
                ),
                metadata={
                    "kind": "connector",
                    "hardware_identifier": (connector.identifier),
                    "board_edge": connector.board_edge,
                    "width_mm": connector.width_mm,
                    "depth_mm": connector.depth_mm,
                    "height_mm": connector.height_mm,
                },
                clearance_envelope=ClearanceEnvelope.for_edge(
                    edge=connector.board_edge,
                    clearance_mm=resolved.usb_access_clearance_mm,
                ),
            ),
            AssemblyComponent(
                identifier="display",
                geometry=_build_display_proxy(),
                placement=Placement(
                    x_mm=resolved.display_x_mm,
                    y_mm=resolved.display_y_mm,
                    z_mm=resolved.display_z_mm,
                ),
                metadata={
                    "kind": "display",
                    "hardware_identifier": (display.identifier),
                    "width_mm": (display.module_width_mm),
                    "depth_mm": (display.module_height_mm),
                    "height_mm": (display.module_depth_mm),
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
