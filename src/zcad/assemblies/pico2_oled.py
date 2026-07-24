"""Reusable Raspberry Pi Pico 2 and OLED device assembly."""

from dataclasses import dataclass

import cadquery as cq
from zcad_core.assemblies import (
    AssemblyComponent,
    DeviceAssembly,
    Placement,
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

    def validate(self) -> None:
        """Validate component elevations."""
        if self.board_z_mm < 0:
            raise ValueError("board_z_mm must not be negative")

        if self.display_z_mm < 0:
            raise ValueError("display_z_mm must not be negative")


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


def build_pico2_oled_assembly(
    parameters: Pico2OledAssemblyParameters | None = None,
) -> DeviceAssembly:
    """Build the reusable Pico 2 and OLED device assembly."""
    resolved = parameters if parameters is not None else Pico2OledAssemblyParameters()

    resolved.validate()

    board = get_raspberry_pi_pico2()
    display = get_reference_oled_128x64()

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
                    "hardware_identifier": (board.identifier),
                    "width_mm": (board.board_width_mm),
                    "depth_mm": (board.board_length_mm),
                    "height_mm": (board.board_thickness_mm),
                },
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
