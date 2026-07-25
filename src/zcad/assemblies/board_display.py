"""Shared rectangular board and display product adapter."""

from dataclasses import dataclass

from zcad_core.assemblies import (
    DeviceAssembly,
    InterferenceReport,
    Placement,
    RectangularBoardSpec,
    RectangularDisplaySpec,
    analyze_board_display_assembly,
    build_board_display_assembly,
)


@dataclass(frozen=True)
class BoardDisplayAssemblyParameters:
    """Placements and clearances for a board-display product."""

    board_x_mm: float = 0.0
    board_y_mm: float = 0.0
    board_z_mm: float = 3.0

    display_x_mm: float = 0.0
    display_y_mm: float = 0.0
    display_z_mm: float = 8.0

    board_display_clearance_mm: float = 0.5
    usb_access_clearance_mm: float = 2.0

    def validate(self) -> None:
        """Validate product placement and clearance parameters."""
        if self.board_z_mm < 0:
            raise ValueError("board_z_mm must not be negative")

        if self.display_z_mm < 0:
            raise ValueError("display_z_mm must not be negative")

        if self.board_display_clearance_mm < 0:
            raise ValueError("board_display_clearance_mm must not be negative")

        if self.usb_access_clearance_mm < 0:
            raise ValueError("usb_access_clearance_mm must not be negative")


def build_board_display_product_assembly(
    *,
    board: RectangularBoardSpec,
    display: RectangularDisplaySpec,
    parameters: BoardDisplayAssemblyParameters,
    connector_identifier: str = "usb_connector",
) -> DeviceAssembly:
    """Build a product assembly from selected board and display hardware."""
    parameters.validate()

    return build_board_display_assembly(
        board=board,
        display=display,
        board_placement=Placement(
            x_mm=parameters.board_x_mm,
            y_mm=parameters.board_y_mm,
            z_mm=parameters.board_z_mm,
        ),
        display_placement=Placement(
            x_mm=parameters.display_x_mm,
            y_mm=parameters.display_y_mm,
            z_mm=parameters.display_z_mm,
        ),
        board_display_clearance_mm=(parameters.board_display_clearance_mm),
        connector_access_clearance_mm=(parameters.usb_access_clearance_mm),
        connector_identifier=connector_identifier,
    )


def analyze_board_display_product_assembly(
    assembly: DeviceAssembly,
    *,
    minimum_board_display_clearance_mm: float = 0.5,
    connector_identifier: str = "usb_connector",
) -> InterferenceReport:
    """Analyze a board-display product assembly."""
    return analyze_board_display_assembly(
        assembly,
        minimum_board_display_clearance_mm=(minimum_board_display_clearance_mm),
        connector_identifier=connector_identifier,
    )


@dataclass(frozen=True)
class BoardDisplayProduct:
    """Declarative definition of a board-display product."""

    identifier: str
    board: RectangularBoardSpec
    display: RectangularDisplaySpec
    default_parameters: BoardDisplayAssemblyParameters
    connector_identifier: str = "usb_connector"

    def validate(self) -> None:
        """Validate the product definition."""
        if not self.identifier.strip():
            raise ValueError("identifier must not be empty")

        if not self.connector_identifier.strip():
            raise ValueError("connector_identifier must not be empty")

        self.default_parameters.validate()


def build_board_display_product(
    product: BoardDisplayProduct,
    *,
    parameters: BoardDisplayAssemblyParameters | None = None,
) -> DeviceAssembly:
    """Build an assembly from a declarative product definition."""
    product.validate()

    resolved = parameters if parameters is not None else product.default_parameters

    return build_board_display_product_assembly(
        board=product.board,
        display=product.display,
        parameters=resolved,
        connector_identifier=product.connector_identifier,
    )


def analyze_board_display_product(
    product: BoardDisplayProduct,
    assembly: DeviceAssembly,
    *,
    minimum_board_display_clearance_mm: float = 0.5,
) -> InterferenceReport:
    """Analyze an assembly using its product definition."""
    product.validate()

    return analyze_board_display_product_assembly(
        assembly,
        minimum_board_display_clearance_mm=(minimum_board_display_clearance_mm),
        connector_identifier=product.connector_identifier,
    )
