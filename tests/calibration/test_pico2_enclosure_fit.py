"""Tests for the refined Pico 2 enclosure assembly."""

import cadquery as cq
import pytest

from zcad.generators.calibration.pico2_enclosure_fit import (
    Pico2EnclosureFitParameters,
    _analyze_usb_access_clearance,
    _connector_cutout_parameters,
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

    from zcad.assemblies import analyze_pico2_oled_assembly

    assert not analyze_pico2_oled_assembly(
        assembly,
        minimum_board_display_clearance_mm=parameters.board_display_clearance_mm,
    ).has_findings
    assert display.transformed_geometry().val().BoundingBox().zmax <= (
        parameters.body_height_mm
    )


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


def test_usb_cutout_follows_assembly_connector() -> None:
    parameters = Pico2EnclosureFitParameters()
    connector = parameters.device_assembly.get("usb_connector")

    cutout = _connector_cutout_parameters(parameters)

    assert cutout.edge == (connector.metadata["board_edge"])
    assert cutout.center_offset_mm == pytest.approx(connector.placement.x_mm)
    assert cutout.bottom_z_mm == pytest.approx(connector.placement.z_mm)

    assert cutout.width_mm == pytest.approx(float(connector.metadata["width_mm"]))
    assert cutout.height_mm == pytest.approx(float(connector.metadata["height_mm"]))

    assert cutout.opening_width_mm == pytest.approx(
        float(connector.metadata["width_mm"]) + parameters.usb_width_clearance_mm
    )
    assert cutout.opening_height_mm == pytest.approx(
        float(connector.metadata["height_mm"]) + parameters.usb_height_clearance_mm
    )


def test_usb_cutout_elevation_follows_standoff_height() -> None:
    lower = Pico2EnclosureFitParameters(
        standoff_height_mm=3.0,
    )
    higher = Pico2EnclosureFitParameters(
        standoff_height_mm=4.0,
    )

    lower_cutout = _connector_cutout_parameters(lower)
    higher_cutout = _connector_cutout_parameters(higher)

    assert higher_cutout.bottom_z_mm == pytest.approx(lower_cutout.bottom_z_mm + 1.0)


def test_default_usb_access_clearance_meets_wall() -> None:
    parameters = Pico2EnclosureFitParameters()

    report = _analyze_usb_access_clearance(parameters)

    assert not report.has_findings


def test_larger_usb_access_clearance_expands_enclosure_depth() -> None:
    default = Pico2EnclosureFitParameters(
        usb_access_clearance_mm=2.0,
    )
    larger = Pico2EnclosureFitParameters(
        usb_access_clearance_mm=4.0,
    )

    assert larger.inner_depth_mm > default.inner_depth_mm
    assert larger.outer_depth_mm > default.outer_depth_mm

    report = _analyze_usb_access_clearance(larger)

    assert not report.has_findings


def test_negative_usb_access_clearance_is_rejected() -> None:
    parameters = Pico2EnclosureFitParameters(
        usb_access_clearance_mm=-0.1,
    )

    with pytest.raises(
        ValueError,
        match="usb_access_clearance_mm",
    ):
        build_pico2_enclosure_fit(parameters)


def test_catalogued_parts_raise_display_and_enclosure() -> None:
    parameters = Pico2EnclosureFitParameters()
    display = parameters.device_assembly.get("display")
    chip = parameters.device_assembly.get("board_top-01")
    gap = display.transformed_geometry().val().BoundingBox().zmin - (
        chip.transformed_geometry().val().BoundingBox().zmax
    )
    assert gap >= parameters.board_display_clearance_mm
    assert (
        parameters.body_height_mm > parameters.floor_mm + parameters.internal_height_mm
    )
    parts = build_pico2_enclosure_fit(parameters)
    # The raised cavity must not leave solid material obstructing the chip.
    chip_shape = chip.transformed_geometry()
    assert parts["body"].intersect(chip_shape).val().Volume() == pytest.approx(0.0)


def test_complete_assembly_clears_body_and_seated_lid() -> None:
    parameters = Pico2EnclosureFitParameters()
    parts = build_pico2_enclosure_fit(parameters)
    seated_lid = parts["lid"].translate(
        (0.0, 0.0, parameters.body_height_mm - parameters.lid_lip_height_mm)
    )
    for component in parameters.device_assembly:
        geometry = component.transformed_geometry()
        for enclosure_part in (parts["body"], seated_lid):
            overlap = enclosure_part.intersect(geometry).val().Volume()
            assert overlap <= 1e-6, component.identifier
    assert parts["body"].intersect(seated_lid).val().Volume() <= 1e-6


def custom_display_data():
    return {
        "identifier": "SYNTHETIC_PICO_CALIBRATION",
        "module_width_mm": 36.0,
        "module_height_mm": 32.0,
        "module_depth_mm": 7.0,
        "active_width_mm": 24.0,
        "active_height_mm": 12.0,
        "active_center_x_mm": 3.0,
        "active_center_y_mm": 2.0,
        "geometry_source": "synthetic test fixture; not a purchased OLED",
    }


def test_custom_display_sizes_body_and_preserves_hardware_clearance():
    parameters = Pico2EnclosureFitParameters(display=custom_display_data())
    default = Pico2EnclosureFitParameters()
    assert parameters.outer_width_mm > default.outer_width_mm
    assert parameters.body_height_mm > default.body_height_mm
    assert (
        parameters.device_assembly.get("display").metadata["hardware_identifier"]
        == "SYNTHETIC_PICO_CALIBRATION"
    )
    parts = build_pico2_enclosure_fit(parameters)
    seated_lid = parts["lid"].translate(
        (0, 0, parameters.body_height_mm - parameters.lid_lip_height_mm)
    )
    for component in parameters.device_assembly:
        for part in (parts["body"], seated_lid):
            assert (
                part.intersect(component.transformed_geometry()).val().Volume() <= 1e-6
            ), component.identifier
    assert parts["body"].intersect(seated_lid).val().Volume() <= 1e-6
    # Full active opening is clear at its offset; adjacent plate remains solid.
    x = parameters.display_center_x_mm + 3
    y = parameters.display_center_y_mm + 2
    z = parameters.lid_lip_height_mm
    opening = (
        cq.Workplane("XY")
        .box(23, 11, parameters.lid_thickness_mm, centered=(True, True, False))
        .translate((x, y, z))
    )
    assert parts["lid"].intersect(opening).val().Volume() <= 1e-6
    outside = (
        cq.Workplane("XY")
        .box(0.2, 0.2, parameters.lid_thickness_mm, centered=(True, True, False))
        .translate((x + 13, y, z))
    )
    assert parts["lid"].intersect(outside).val().Volume() > 0


def test_custom_display_input_is_frozen_and_records_source():
    data = custom_display_data()
    parameters = Pico2EnclosureFitParameters(display=data)
    data["module_width_mm"] = 100
    assert parameters.display_spec.module_width_mm == 36
    assert (
        parameters.display_spec.geometry_source
        == "synthetic test fixture; not a purchased OLED"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("module_depth_mm", float("nan")),
        ("geometry_source", ""),
        ("module_width_mm", -1),
    ],
)
def test_custom_display_rejects_bad_input(field, value):
    data = custom_display_data()
    data[field] = value
    with pytest.raises(ValueError):
        Pico2EnclosureFitParameters(display=data)


def test_retained_display_has_valid_lid_and_clear_board_components():
    parameters = Pico2EnclosureFitParameters(display_retention="clips")
    parts = build_pico2_enclosure_fit(parameters)
    seated = parts["lid"].translate(
        (0, 0, parameters.body_height_mm - parameters.lid_lip_height_mm)
    )
    assert len(parts["lid"].val().Solids()) == 1
    assert parts["lid"].val().BoundingBox().zlen == pytest.approx(
        parameters.lid_overall_height_mm
    )
    for component in parameters.device_assembly:
        assert seated.intersect(component.transformed_geometry()).val().Volume() <= 1e-6
    assert seated.intersect(parts["body"]).val().Volume() <= 1e-6
    retainer = parameters.retention_parameters
    # Material exists under both module edges; middle header edges stay open.
    for side in (-1, 1):
        point = cq.Vector(
            side * (retainer.module_width_mm / 2 - 0.4),
            retainer.center_y_mm,
            retainer.module_bottom_z_mm - retainer.clip_gap_mm - 0.5,
        )
        assert seated.val().isInside(point)
        header = cq.Vector(
            0,
            retainer.center_y_mm + side * (retainer.module_depth_mm / 2 + 0.6),
            retainer.module_top_z_mm - 1,
        )
        assert not seated.val().isInside(header)


@pytest.mark.parametrize(
    "options,message",
    [
        ({"display_retention": "unknown"}, "display_retention"),
        (
            {"display_retention": "clips", "retention_clip_reach_mm": 0.2},
            "clip_reach_mm",
        ),
        (
            {"display_retention": "clips", "retention_clip_gap_mm": -0.1},
            "retention_clip_gap_mm",
        ),
    ],
)
def test_invalid_retention_is_rejected(options, message):
    with pytest.raises(ValueError, match=message):
        build_pico2_enclosure_fit(Pico2EnclosureFitParameters(**options))


def test_layered_display_requires_pcb_specific_support():
    data = custom_display_data()
    data.update(
        pcb_thickness_mm=1, panel_width_mm=30, panel_height_mm=20, panel_thickness_mm=1
    )
    with pytest.raises(ValueError, match="layered modules"):
        build_pico2_enclosure_fit(
            Pico2EnclosureFitParameters(display=data, display_retention="clips")
        )
