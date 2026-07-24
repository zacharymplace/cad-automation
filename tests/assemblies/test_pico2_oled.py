"""Tests for the reusable Pico 2 and OLED assembly."""

import pytest

from zcad.assemblies import (
    Pico2OledAssemblyParameters,
    build_pico2_oled_assembly,
)


def test_assembly_contains_board_connector_and_display() -> None:
    assembly = build_pico2_oled_assembly()

    assert assembly.identifiers == (
        "board",
        "usb_connector",
        "display",
    )

    assert assembly.get("board").metadata["kind"] == "pcb"
    assert assembly.get("usb_connector").metadata["kind"] == "connector"
    assert assembly.get("display").metadata["kind"] == "display"


def test_default_component_placements() -> None:
    assembly = build_pico2_oled_assembly()

    board = assembly.get("board")
    connector = assembly.get("usb_connector")
    display = assembly.get("display")

    assert board.placement.z_mm == pytest.approx(3.0)
    assert connector.placement.x_mm == pytest.approx(0.0)
    assert connector.placement.y_mm == pytest.approx(-22.4625)
    assert connector.placement.z_mm == pytest.approx(4.0)
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
    assert len(compound.Solids()) == 3


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
        match="exactly board, usb_connector, and display",
    ):
        analyze_pico2_oled_assembly(assembly)


def test_board_carries_positive_z_clearance_envelope() -> None:
    assembly = build_pico2_oled_assembly(
        Pico2OledAssemblyParameters(
            board_display_clearance_mm=1.25,
        )
    )

    board = assembly.get("board")

    assert board.clearance_envelope.positive_z_mm == pytest.approx(1.25)
    assert board.clearance_envelope.negative_z_mm == pytest.approx(0.0)


def test_generic_core_analyzer_consumes_board_envelope() -> None:
    assembly = build_pico2_oled_assembly(
        Pico2OledAssemblyParameters(
            display_z_mm=4.25,
            board_display_clearance_mm=0.5,
        )
    )

    from zcad_core.assemblies import component_pair

    report = assembly.analyze_interference(
        allowed_contact_pairs=(
            component_pair(
                "board",
                "usb_connector",
            ),
        )
    )

    assert not report.collisions
    assert len(report.clearance_violations) == 1

    finding = report.clearance_violations[0]

    assert finding.clearance_source == "envelope"
    assert finding.measured_clearance_mm == pytest.approx(0.25)
    assert finding.required_clearance_mm == pytest.approx(0.5)


def test_negative_embedded_clearance_is_rejected() -> None:
    parameters = Pico2OledAssemblyParameters(
        board_display_clearance_mm=-0.1,
    )

    with pytest.raises(
        ValueError,
        match="board_display_clearance_mm",
    ):
        build_pico2_oled_assembly(parameters)


def test_policy_wrapper_does_not_mutate_assembly() -> None:
    from zcad.assemblies import (
        analyze_pico2_oled_assembly,
    )

    assembly = build_pico2_oled_assembly(
        Pico2OledAssemblyParameters(
            display_z_mm=4.5,
            board_display_clearance_mm=0.5,
        )
    )

    board = assembly.get("board")
    embedded_envelope = board.clearance_envelope

    report = analyze_pico2_oled_assembly(
        assembly,
        minimum_board_display_clearance_mm=2.0,
    )

    assert len(report.clearance_violations) == 1
    assert report.clearance_violations[0].required_clearance_mm == pytest.approx(2.0)

    assert assembly.get("board") is board
    assert board.clearance_envelope is embedded_envelope
    assert embedded_envelope.positive_z_mm == pytest.approx(0.5)


def test_usb_connector_uses_catalog_body_dimensions() -> None:
    assembly = build_pico2_oled_assembly()
    connector = assembly.get("usb_connector")

    bounds = connector.transformed_geometry().val().BoundingBox()

    assert bounds.xlen == pytest.approx(8.9)
    assert bounds.ylen == pytest.approx(6.075)
    assert bounds.zlen == pytest.approx(3.2)

    assert connector.metadata["hardware_identifier"] == "USB_MICRO_B"
    assert connector.metadata["board_edge"] == "negative_y"


def test_policy_allows_board_connector_attachment() -> None:
    from zcad.assemblies import (
        analyze_pico2_oled_assembly,
    )

    report = analyze_pico2_oled_assembly(build_pico2_oled_assembly())

    assert not report.has_findings


def test_generic_analysis_requires_attachment_exception() -> None:
    from zcad_core.assemblies import component_pair

    assembly = build_pico2_oled_assembly()

    report = assembly.analyze_interference(
        allowed_contact_pairs=(
            component_pair(
                "board",
                "usb_connector",
            ),
        )
    )

    assert not report.has_findings
