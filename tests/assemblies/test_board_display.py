"""Tests for the shared board-display product adapter."""

from dataclasses import dataclass, field

import pytest
from zcad_core.hardware import RectangularConnectorSpec

from zcad.assemblies.board_display import (
    BoardDisplayAssemblyParameters,
    BoardDisplayProduct,
    analyze_board_display_product,
    analyze_board_display_product_assembly,
    build_board_display_product,
    build_board_display_product_assembly,
)


def _connector() -> RectangularConnectorSpec:
    return RectangularConnectorSpec(
        identifier="TEST_USB",
        width_mm=8.0,
        height_mm=3.0,
        depth_mm=6.0,
        board_edge="positive_y",
    )


@dataclass(frozen=True)
class FixtureBoardSpec:
    identifier: str = "TEST_BOARD"
    board_width_mm: float = 18.0
    board_length_mm: float = 24.0
    board_thickness_mm: float = 1.0
    usb_connector: RectangularConnectorSpec = field(default_factory=_connector)


@dataclass(frozen=True)
class FixtureDisplaySpec:
    identifier: str = "TEST_DISPLAY"
    module_width_mm: float = 28.0
    module_height_mm: float = 15.0
    module_depth_mm: float = 4.0
    mount_style: str = "test"


def test_shared_adapter_builds_selected_hardware() -> None:
    assembly = build_board_display_product_assembly(
        board=FixtureBoardSpec(),
        display=FixtureDisplaySpec(),
        parameters=BoardDisplayAssemblyParameters(
            display_y_mm=3.0,
        ),
    )

    assert assembly.identifiers == (
        "board",
        "usb_connector",
        "display",
    )

    assert assembly.get("board").metadata["hardware_identifier"] == "TEST_BOARD"
    assert assembly.get("usb_connector").metadata["hardware_identifier"] == "TEST_USB"
    assert assembly.get("display").metadata["hardware_identifier"] == "TEST_DISPLAY"


def test_shared_adapter_preserves_placements() -> None:
    assembly = build_board_display_product_assembly(
        board=FixtureBoardSpec(),
        display=FixtureDisplaySpec(),
        parameters=BoardDisplayAssemblyParameters(
            board_x_mm=1.0,
            board_y_mm=2.0,
            board_z_mm=3.0,
            display_x_mm=4.0,
            display_y_mm=5.0,
            display_z_mm=8.0,
        ),
    )

    board = assembly.get("board")
    display = assembly.get("display")

    assert board.placement.x_mm == pytest.approx(1.0)
    assert board.placement.y_mm == pytest.approx(2.0)
    assert board.placement.z_mm == pytest.approx(3.0)

    assert display.placement.x_mm == pytest.approx(4.0)
    assert display.placement.y_mm == pytest.approx(5.0)
    assert display.placement.z_mm == pytest.approx(8.0)


def test_shared_adapter_applies_connector_access_clearance() -> None:
    assembly = build_board_display_product_assembly(
        board=FixtureBoardSpec(),
        display=FixtureDisplaySpec(),
        parameters=BoardDisplayAssemblyParameters(
            usb_access_clearance_mm=2.5,
        ),
    )

    envelope = assembly.get("usb_connector").clearance_envelope

    assert envelope.positive_y_mm == pytest.approx(2.5)


def test_shared_adapter_rejects_invalid_parameters() -> None:
    with pytest.raises(
        ValueError,
        match="board_z_mm",
    ):
        build_board_display_product_assembly(
            board=FixtureBoardSpec(),
            display=FixtureDisplaySpec(),
            parameters=BoardDisplayAssemblyParameters(
                board_z_mm=-0.1,
            ),
        )


def test_shared_adapter_analysis_passes_valid_assembly() -> None:
    assembly = build_board_display_product_assembly(
        board=FixtureBoardSpec(),
        display=FixtureDisplaySpec(),
        parameters=BoardDisplayAssemblyParameters(
            display_y_mm=-8.0,
            display_z_mm=5.0,
        ),
    )

    report = analyze_board_display_product_assembly(
        assembly,
        minimum_board_display_clearance_mm=0.0,
    )

    assert not report.has_findings


def _product() -> BoardDisplayProduct:
    return BoardDisplayProduct(
        identifier="TEST_BOARD_DISPLAY",
        board=FixtureBoardSpec(),
        display=FixtureDisplaySpec(),
        default_parameters=BoardDisplayAssemblyParameters(
            display_y_mm=-8.0,
            display_z_mm=5.0,
        ),
    )


def test_declarative_product_builds_default_assembly() -> None:
    assembly = build_board_display_product(_product())

    assert assembly.identifiers == (
        "board",
        "usb_connector",
        "display",
    )
    assert assembly.get("board").metadata["hardware_identifier"] == "TEST_BOARD"
    assert assembly.get("display").placement.y_mm == pytest.approx(-8.0)


def test_declarative_product_accepts_parameter_override() -> None:
    assembly = build_board_display_product(
        _product(),
        parameters=BoardDisplayAssemblyParameters(
            display_y_mm=-10.0,
            display_z_mm=6.0,
        ),
    )

    assert assembly.get("display").placement.y_mm == pytest.approx(-10.0)
    assert assembly.get("display").placement.z_mm == pytest.approx(6.0)


def test_declarative_product_analysis_passes() -> None:
    product = _product()
    assembly = build_board_display_product(product)

    report = analyze_board_display_product(
        product,
        assembly,
        minimum_board_display_clearance_mm=0.0,
    )

    assert not report.has_findings


@pytest.mark.parametrize(
    ("identifier", "connector_identifier", "message"),
    [
        ("", "usb_connector", "identifier"),
        ("TEST_PRODUCT", "", "connector_identifier"),
    ],
)
def test_declarative_product_rejects_invalid_identifiers(
    identifier: str,
    connector_identifier: str,
    message: str,
) -> None:
    product = BoardDisplayProduct(
        identifier=identifier,
        board=FixtureBoardSpec(),
        display=FixtureDisplaySpec(),
        default_parameters=BoardDisplayAssemblyParameters(),
        connector_identifier=connector_identifier,
    )

    with pytest.raises(ValueError, match=message):
        build_board_display_product(product)
