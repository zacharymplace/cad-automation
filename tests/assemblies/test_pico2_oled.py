"""Tests for the reusable Pico 2 and OLED assembly."""

import pytest

from zcad.assemblies import (
    Pico2OledAssemblyParameters,
    build_pico2_oled_assembly,
)


def test_assembly_contains_board_and_display() -> None:
    assembly = build_pico2_oled_assembly()

    assert assembly.identifiers == (
        "board",
        "display",
    )

    assert assembly.get("board").metadata["kind"] == "pcb"

    assert assembly.get("display").metadata["kind"] == "display"


def test_default_component_placements() -> None:
    assembly = build_pico2_oled_assembly()

    board = assembly.get("board")
    display = assembly.get("display")

    assert board.placement.z_mm == pytest.approx(3.0)
    assert display.placement.y_mm == pytest.approx(6.0)
    assert display.placement.z_mm == pytest.approx(8.0)


def test_default_assembly_bounds() -> None:
    assembly = build_pico2_oled_assembly()
    bounds = assembly.bounds()

    assert bounds.width_mm == pytest.approx(28.0)
    assert bounds.depth_mm == pytest.approx(51.0)
    assert bounds.height_mm == pytest.approx(9.0)

    assert bounds.minimum_z_mm == pytest.approx(3.0)
    assert bounds.maximum_z_mm == pytest.approx(12.0)


def test_custom_placements_change_bounds() -> None:
    assembly = build_pico2_oled_assembly(
        Pico2OledAssemblyParameters(
            display_x_mm=20.0,
            display_y_mm=0.0,
            display_z_mm=10.0,
        )
    )

    bounds = assembly.bounds()

    assert bounds.width_mm > 28.0
    assert bounds.maximum_z_mm == pytest.approx(14.0)


def test_negative_board_elevation_is_rejected() -> None:
    parameters = Pico2OledAssemblyParameters(
        board_z_mm=-0.1,
    )

    with pytest.raises(
        ValueError,
        match="board_z_mm",
    ):
        build_pico2_oled_assembly(parameters)


def test_assembly_compound_is_valid() -> None:
    assembly = build_pico2_oled_assembly()
    compound = assembly.compound().val()

    assert compound.isValid()
    assert len(compound.Solids()) == 2
