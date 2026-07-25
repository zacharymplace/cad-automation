"""Seeed XIAO ESP32-S3 and OLED product assembly adapter."""

from dataclasses import dataclass

from zcad_core.assemblies import (
    DeviceAssembly,
    InterferenceReport,
)
from zcad_core.hardware import (
    get_reference_oled_128x64,
    get_seeed_xiao_esp32s3,
)

from zcad.assemblies.board_display import (
    BoardDisplayAssemblyParameters,
    BoardDisplayProduct,
    analyze_board_display_product,
    build_board_display_product,
)


@dataclass(frozen=True)
class XiaoEsp32S3OledAssemblyParameters(BoardDisplayAssemblyParameters):
    """Placements for a XIAO ESP32-S3 and OLED assembly."""

    display_y_mm: float = -6.0


XIAO_ESP32S3_OLED_PRODUCT = BoardDisplayProduct(
    identifier="XIAO_ESP32S3_OLED",
    board=get_seeed_xiao_esp32s3(),
    display=get_reference_oled_128x64(),
    default_parameters=XiaoEsp32S3OledAssemblyParameters(),
)


def build_xiao_esp32s3_oled_assembly(
    parameters: XiaoEsp32S3OledAssemblyParameters | None = None,
) -> DeviceAssembly:
    """Build the XIAO ESP32-S3, USB-C, and OLED assembly."""
    return build_board_display_product(
        XIAO_ESP32S3_OLED_PRODUCT,
        parameters=parameters,
    )


def analyze_xiao_esp32s3_oled_assembly(
    assembly: DeviceAssembly,
    *,
    minimum_board_display_clearance_mm: float = 0.5,
) -> InterferenceReport:
    """Analyze XIAO attachment and display-clearance policy."""
    try:
        return analyze_board_display_product(
            XIAO_ESP32S3_OLED_PRODUCT,
            assembly,
            minimum_board_display_clearance_mm=(minimum_board_display_clearance_mm),
        )
    except ValueError as error:
        if "board-display assembly must contain exactly" not in str(error):
            raise

        raise ValueError(
            "XIAO ESP32-S3 OLED assembly must contain exactly "
            "board, usb_connector, and display components"
        ) from error
