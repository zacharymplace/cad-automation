"""Raspberry Pi Pico 2 and OLED product assembly adapter."""

from dataclasses import dataclass

from zcad_core.assemblies import (
    DeviceAssembly,
    InterferenceReport,
)
from zcad_core.hardware import (
    get_raspberry_pi_pico2,
    get_reference_oled_128x64,
)

from zcad.assemblies.board_display import (
    BoardDisplayAssemblyParameters,
    analyze_board_display_product_assembly,
    build_board_display_product_assembly,
)


@dataclass(frozen=True)
class Pico2OledAssemblyParameters(BoardDisplayAssemblyParameters):
    """Authoritative placements for a Pico 2 and OLED assembly."""

    display_y_mm: float = 6.0


def build_pico2_oled_assembly(
    parameters: Pico2OledAssemblyParameters | None = None,
) -> DeviceAssembly:
    """Build the Pico 2, USB, and OLED product assembly."""
    resolved = parameters if parameters is not None else Pico2OledAssemblyParameters()

    return build_board_display_product_assembly(
        board=get_raspberry_pi_pico2(),
        display=get_reference_oled_128x64(),
        parameters=resolved,
    )


def analyze_pico2_oled_assembly(
    assembly: DeviceAssembly,
    *,
    minimum_board_display_clearance_mm: float = 0.5,
) -> InterferenceReport:
    """Analyze Pico 2 attachment and display-clearance policy."""
    try:
        return analyze_board_display_product_assembly(
            assembly,
            minimum_board_display_clearance_mm=(minimum_board_display_clearance_mm),
        )
    except ValueError as error:
        if "board-display assembly must contain exactly" not in str(error):
            raise

        raise ValueError(
            "Pico 2 OLED assembly must contain exactly "
            "board, usb_connector, and display components"
        ) from error
