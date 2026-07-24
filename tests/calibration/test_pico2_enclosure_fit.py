"""Tests for the refined Pico 2 enclosure assembly."""

import cadquery as cq
import pytest

from zcad.generators.calibration.pico2_enclosure_fit import (
    Pico2EnclosureFitParameters,
    build_pico2_enclosure_fit,
)


def test_enclosure_returns_body_and_lid() -> None:
    parts = build_pico2_enclosure_fit(Pico2EnclosureFitParameters())

    assert set(parts) == {
        "body",
        "lid",
    }

    for part in parts.values():
        assert isinstance(part, cq.Workplane)
        assert part.val().isValid()
        assert part.val().Volume() > 0


def test_body_dimensions() -> None:
    parameters = Pico2EnclosureFitParameters()
    parts = build_pico2_enclosure_fit(parameters)

    bounds = parts["body"].val().BoundingBox()

    assert bounds.xlen == pytest.approx(parameters.outer_width_mm)
    assert bounds.ylen == pytest.approx(parameters.outer_depth_mm)
    assert bounds.zlen == pytest.approx(parameters.body_height_mm)


def test_lid_matches_body_footprint() -> None:
    parameters = Pico2EnclosureFitParameters()
    parts = build_pico2_enclosure_fit(parameters)

    body_bounds = parts["body"].val().BoundingBox()
    lid_bounds = parts["lid"].val().BoundingBox()

    assert lid_bounds.xlen == pytest.approx(body_bounds.xlen)
    assert lid_bounds.ylen == pytest.approx(body_bounds.ylen)
    assert parameters.lid_height_mm == pytest.approx(
        parameters.lid_lip_height_mm + parameters.lid_thickness_mm
    )
    assert lid_bounds.zlen == pytest.approx(parameters.lid_overall_height_mm)


def test_corner_radius_can_be_disabled() -> None:
    parts = build_pico2_enclosure_fit(
        Pico2EnclosureFitParameters(
            corner_radius_mm=0.0,
            exterior_edge_fillet_mm=0.0,
        )
    )

    assert parts["body"].val().isValid()
    assert parts["lid"].val().isValid()


def test_invalid_lid_clearance_is_rejected() -> None:
    parameters = Pico2EnclosureFitParameters(
        lid_clearance_mm=-0.1,
    )

    with pytest.raises(
        ValueError,
        match="lid_clearance_mm",
    ):
        build_pico2_enclosure_fit(parameters)


def test_excessive_corner_radius_is_rejected() -> None:
    parameters = Pico2EnclosureFitParameters(
        corner_radius_mm=20.0,
    )

    with pytest.raises(
        ValueError,
        match="corner_radius_mm",
    ):
        build_pico2_enclosure_fit(parameters)


def test_display_expands_enclosure_width() -> None:
    parameters = Pico2EnclosureFitParameters()
    board_only_width_mm = (
        21.0 + (2 * parameters.board_clearance_mm) + (2 * parameters.wall_mm)
    )

    assert parameters.outer_width_mm > board_only_width_mm


def test_lid_contains_display_window() -> None:
    parameters = Pico2EnclosureFitParameters()
    parts = build_pico2_enclosure_fit(parameters)

    lid = parts["lid"].val()

    full_plate_volume_mm3 = (
        parameters.outer_width_mm
        * parameters.outer_depth_mm
        * parameters.lid_thickness_mm
    )

    assert lid.isValid()
    assert lid.Volume() > 0
    assert lid.Volume() < (full_plate_volume_mm3 + 2000.0)


def test_shifted_display_expands_enclosure() -> None:
    centered = Pico2EnclosureFitParameters(
        display_center_x_mm=0.0,
    )
    shifted = Pico2EnclosureFitParameters(
        display_center_x_mm=20.0,
    )

    build_pico2_enclosure_fit(centered)
    shifted_parts = build_pico2_enclosure_fit(shifted)

    assert shifted.inner_width_mm > centered.inner_width_mm
    assert shifted.outer_width_mm > centered.outer_width_mm

    assert shifted_parts["body"].val().BoundingBox().xlen == pytest.approx(
        shifted.outer_width_mm
    )

    assert shifted_parts["lid"].val().BoundingBox().xlen == pytest.approx(
        shifted.outer_width_mm
    )


def test_enclosure_exposes_authoritative_assembly() -> None:
    parameters = Pico2EnclosureFitParameters(
        display_center_x_mm=2.0,
        display_center_y_mm=7.0,
    )

    assembly = parameters.device_assembly

    board = assembly.get("board")
    connector = assembly.get("usb_connector")
    display = assembly.get("display")

    assert board.placement.z_mm == pytest.approx(
        parameters.floor_mm + parameters.standoff_height_mm
    )

    assert connector.placement.z_mm == pytest.approx(
        board.placement.z_mm + float(board.metadata["height_mm"])
    )
    assert connector.metadata["kind"] == "connector"

    assert display.placement.x_mm == pytest.approx(2.0)
    assert display.placement.y_mm == pytest.approx(7.0)

    board_top_z_mm = board.placement.z_mm + float(board.metadata["height_mm"])

    nominal_display_z_mm = parameters.body_height_mm - float(
        display.metadata["height_mm"]
    )

    expected_display_z_mm = max(
        nominal_display_z_mm,
        board_top_z_mm + parameters.board_display_clearance_mm,
    )

    assert display.placement.z_mm == pytest.approx(expected_display_z_mm)


def test_enclosure_width_comes_from_assembly() -> None:
    parameters = Pico2EnclosureFitParameters(
        display_center_x_mm=5.0,
    )

    display = parameters.device_assembly.get("display")

    expected_display_width_mm = 2 * (
        abs(display.placement.x_mm)
        + (float(display.metadata["width_mm"]) / 2)
        + parameters.display_module_clearance_mm
        + parameters.lid_clearance_mm
        + parameters.lid_lip_wall_mm
    )

    assert parameters.inner_width_mm == pytest.approx(expected_display_width_mm)


def test_display_window_follows_assembly_placement() -> None:
    centered = build_pico2_enclosure_fit(
        Pico2EnclosureFitParameters(
            display_center_x_mm=0.0,
        )
    )["lid"]

    shifted = build_pico2_enclosure_fit(
        Pico2EnclosureFitParameters(
            display_center_x_mm=3.0,
        )
    )["lid"]

    centered_bounds = centered.val().BoundingBox()
    shifted_bounds = shifted.val().BoundingBox()

    assert centered.val().isValid()
    assert shifted.val().isValid()

    assert shifted_bounds.xlen > (centered_bounds.xlen)


def test_enclosure_assembly_embeds_clearance_envelope() -> None:
    parameters = Pico2EnclosureFitParameters(
        board_display_clearance_mm=1.5,
    )

    board = parameters.device_assembly.get("board")

    assert board.clearance_envelope.positive_z_mm == pytest.approx(1.5)


def test_enclosure_assembly_meets_clearance_policy() -> None:
    from zcad.assemblies import (
        analyze_pico2_oled_assembly,
    )

    parameters = Pico2EnclosureFitParameters()

    report = analyze_pico2_oled_assembly(
        parameters.device_assembly,
        minimum_board_display_clearance_mm=(parameters.board_display_clearance_mm),
    )

    assert not report.has_findings


def test_larger_clearance_raises_display() -> None:
    default_parameters = Pico2EnclosureFitParameters(
        board_display_clearance_mm=0.5,
    )
    larger_parameters = Pico2EnclosureFitParameters(
        board_display_clearance_mm=2.0,
    )

    default_display = default_parameters.device_assembly.get("display")
    larger_display = larger_parameters.device_assembly.get("display")

    assert larger_display.placement.z_mm > default_display.placement.z_mm


def test_negative_board_display_clearance_is_rejected() -> None:
    parameters = Pico2EnclosureFitParameters(
        board_display_clearance_mm=-0.1,
    )

    with pytest.raises(
        ValueError,
        match="board_display_clearance_mm",
    ):
        build_pico2_enclosure_fit(parameters)
