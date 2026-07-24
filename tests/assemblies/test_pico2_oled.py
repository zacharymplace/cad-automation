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


def test_default_assembly_passes_clearance_policy() -> None:
    from zcad.assemblies import (
        analyze_pico2_oled_assembly,
    )

    assembly = build_pico2_oled_assembly()

    report = analyze_pico2_oled_assembly(
        assembly,
        minimum_board_display_clearance_mm=0.5,
    )

    assert not report.has_findings


def test_board_display_collision_is_reported() -> None:
    from zcad.assemblies import (
        analyze_pico2_oled_assembly,
    )

    assembly = build_pico2_oled_assembly(
        Pico2OledAssemblyParameters(
            display_z_mm=3.5,
        )
    )

    report = analyze_pico2_oled_assembly(
        assembly,
        minimum_board_display_clearance_mm=0.5,
    )

    assert len(report.collisions) == 1
    assert not report.clearance_violations

    assert report.collisions[0].pair == {
        "board",
        "display",
    }


def test_insufficient_board_display_clearance_is_reported() -> None:
    from zcad.assemblies import (
        analyze_pico2_oled_assembly,
    )

    assembly = build_pico2_oled_assembly(
        Pico2OledAssemblyParameters(
            display_z_mm=4.25,
        )
    )

    report = analyze_pico2_oled_assembly(
        assembly,
        minimum_board_display_clearance_mm=0.5,
    )

    assert not report.collisions
    assert len(report.clearance_violations) == 1

    finding = report.clearance_violations[0]

    assert finding.measured_clearance_mm == pytest.approx(0.25)
    assert finding.required_clearance_mm == pytest.approx(0.5)


def test_exact_board_display_clearance_passes() -> None:
    from zcad.assemblies import (
        analyze_pico2_oled_assembly,
    )

    assembly = build_pico2_oled_assembly(
        Pico2OledAssemblyParameters(
            display_z_mm=4.5,
        )
    )

    report = analyze_pico2_oled_assembly(
        assembly,
        minimum_board_display_clearance_mm=0.5,
    )

    assert not report.has_findings


def test_negative_clearance_policy_is_rejected() -> None:
    from zcad.assemblies import (
        analyze_pico2_oled_assembly,
    )

    assembly = build_pico2_oled_assembly()

    with pytest.raises(
        ValueError,
        match="minimum_board_display_clearance_mm",
    ):
        analyze_pico2_oled_assembly(
            assembly,
            minimum_board_display_clearance_mm=-0.1,
        )


def test_clearance_policy_rejects_wrong_component_set() -> None:
    import cadquery as cq
    from zcad_core.assemblies import (
        AssemblyComponent,
        DeviceAssembly,
    )

    from zcad.assemblies import (
        analyze_pico2_oled_assembly,
    )

    assembly = DeviceAssembly(
        (
            AssemblyComponent(
                identifier="board",
                geometry=cq.Workplane("XY").box(
                    10.0,
                    10.0,
                    1.0,
                    centered=(
                        True,
                        True,
                        False,
                    ),
                ),
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="exactly board and display",
    ):
        analyze_pico2_oled_assembly(assembly)
