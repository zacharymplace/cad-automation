"""Tests for registry-driven board-display enclosure geometry."""

from dataclasses import replace

import pytest

from zcad.designs import (
    parse_board_display_design,
)
from zcad.generators.board_display_enclosure import (
    BoardDisplayEnclosureParameters,
    _build_enclosure_parameters,
    analyze_board_display_enclosure_fit,
    build_board_display_enclosure,
    build_board_display_enclosure_result,
)


@pytest.mark.parametrize(
    "product",
    [
        "PICO2_OLED",
        "XIAO_ESP32S3_OLED",
    ],
)
def test_registered_products_generate_valid_parts(
    product: str,
) -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": product,
        }
    )

    parts = build_board_display_enclosure(design)

    assert set(parts) == {
        "body",
        "lid",
    }

    for part in parts.values():
        value = part.val()

        assert value is not None
        assert value.isValid()
        assert value.Volume() > 0


def test_pico_and_xiao_resolve_different_enclosure_depths() -> None:
    pico = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )
    xiao = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    pico_parameters = _build_enclosure_parameters(
        pico,
        BoardDisplayEnclosureParameters(),
    )
    xiao_parameters = _build_enclosure_parameters(
        xiao,
        BoardDisplayEnclosureParameters(),
    )

    assert pico_parameters.depth > xiao_parameters.depth


def test_enclosure_dimensions_follow_derived_cavity() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )
    policy = BoardDisplayEnclosureParameters(
        wall_mm=2.5,
        floor_mm=2.0,
        internal_clearance_mm=1.5,
    )

    parameters = _build_enclosure_parameters(
        design,
        policy,
    )

    assert parameters.width > 28.0
    assert parameters.depth > 51.0
    assert parameters.height > 12.0
    assert parameters.wall == pytest.approx(2.5)
    assert parameters.floor == pytest.approx(2.0)


def test_connector_dimensions_drive_cable_slot() -> None:
    pico = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )
    xiao = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    policy = BoardDisplayEnclosureParameters(
        connector_cutout_clearance_mm=0.5,
    )

    pico_parameters = _build_enclosure_parameters(
        pico,
        policy,
    )
    xiao_parameters = _build_enclosure_parameters(
        xiao,
        policy,
    )

    assert pico_parameters.cable_slot_width == pytest.approx(9.9)
    assert xiao_parameters.cable_slot_width == pytest.approx(10.0)
    assert pico_parameters.cable_slot_height == pytest.approx(4.2)
    assert xiao_parameters.cable_slot_height == pytest.approx(4.2)


def test_default_label_uses_product_identifier() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    default_parts = build_board_display_enclosure(design)
    explicit_parts = build_board_display_enclosure(
        design,
        BoardDisplayEnclosureParameters(
            label="CUSTOM",
        ),
    )

    assert default_parts["lid"].val().Volume() > 0
    assert explicit_parts["lid"].val().Volume() > 0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("wall_mm", 0.0, "wall_mm"),
        (
            "internal_clearance_mm",
            -0.1,
            "internal_clearance_mm",
        ),
        (
            "connector_cutout_clearance_mm",
            -0.1,
            "connector_cutout_clearance_mm",
        ),
        ("label", " ", "label"),
    ],
)
def test_enclosure_policy_rejects_invalid_values(
    field: str,
    value: object,
    message: str,
) -> None:
    arguments = {
        field: value,
    }

    with pytest.raises(
        ValueError,
        match=message,
    ):
        BoardDisplayEnclosureParameters(
            **arguments,
        ).validate()


def test_connector_edge_drives_enclosure_slot_edge() -> None:
    pico = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )
    xiao = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    policy = BoardDisplayEnclosureParameters()

    pico_parameters = _build_enclosure_parameters(
        pico,
        policy,
    )
    xiao_parameters = _build_enclosure_parameters(
        xiao,
        policy,
    )

    assert pico_parameters.cable_slot_edge == "negative_y"
    assert xiao_parameters.cable_slot_edge == "positive_y"


def test_connector_height_drives_enclosure_slot_offset() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    parameters = _build_enclosure_parameters(
        design,
        BoardDisplayEnclosureParameters(),
    )

    assert parameters.cable_slot_bottom_offset >= 0
    assert (
        parameters.cable_slot_bottom_offset + parameters.cable_slot_height
        <= parameters.height - parameters.floor
    )


@pytest.mark.parametrize(
    "product",
    [
        "PICO2_OLED",
        "XIAO_ESP32S3_OLED",
    ],
)
def test_default_enclosure_fit_passes(
    product: str,
) -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": product,
        }
    )

    build = build_board_display_enclosure_result(design)
    report = analyze_board_display_enclosure_fit(build)

    assert not report.has_findings


def test_enclosure_build_result_preserves_resolved_artifacts() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)

    assert build.assembly.identifiers == (
        "board",
        "usb_connector",
        "display",
    )
    assert build.specification.cable_edge == "negative_y"
    assert set(build.parts) == {
        "body",
        "lid",
    }


def test_fit_analysis_detects_undersized_cavity() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            internal_clearance_mm=0.0,
        ),
    )

    report = analyze_board_display_enclosure_fit(build)

    assert not report.has_findings


def _lid_volume(
    product: str,
    policy: BoardDisplayEnclosureParameters,
) -> float:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": product,
        }
    )

    return (
        build_board_display_enclosure(
            design,
            policy,
        )["lid"]
        .val()
        .Volume()
    )


@pytest.mark.parametrize(
    "product",
    [
        "PICO2_OLED",
        "XIAO_ESP32S3_OLED",
    ],
)
def test_display_window_generates_valid_lid(
    product: str,
) -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": product,
        }
    )

    lid = build_board_display_enclosure(design)["lid"].val()

    assert lid.isValid()
    assert lid.Volume() > 0


def test_display_window_removes_lid_material() -> None:
    enabled = _lid_volume(
        "PICO2_OLED",
        BoardDisplayEnclosureParameters(
            display_window_enabled=True,
        ),
    )
    disabled = _lid_volume(
        "PICO2_OLED",
        BoardDisplayEnclosureParameters(
            display_window_enabled=False,
        ),
    )

    assert enabled < disabled


def test_display_window_clearance_enlarges_opening() -> None:
    small = _lid_volume(
        "PICO2_OLED",
        BoardDisplayEnclosureParameters(
            display_window_clearance_mm=0.0,
        ),
    )
    large = _lid_volume(
        "PICO2_OLED",
        BoardDisplayEnclosureParameters(
            display_window_clearance_mm=1.0,
        ),
    )

    assert large < small


def test_display_window_follows_display_xy_placement() -> None:
    centered = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )
    shifted = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
            "parameters": {
                "display_x_mm": 3.0,
                "display_y_mm": 2.0,
            },
        }
    )

    centered_lid = build_board_display_enclosure(centered)["lid"].val()
    shifted_lid = build_board_display_enclosure(shifted)["lid"].val()

    assert centered_lid.isValid()
    assert shifted_lid.isValid()
    assert shifted_lid.Volume() == pytest.approx(
        centered_lid.Volume(),
        rel=1e-6,
    )


def test_disabling_display_window_preserves_more_material() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    windowed = build_board_display_enclosure(
        design,
        BoardDisplayEnclosureParameters(
            display_window_enabled=True,
        ),
    )["lid"].val()

    solid = build_board_display_enclosure(
        design,
        BoardDisplayEnclosureParameters(
            display_window_enabled=False,
        ),
    )["lid"].val()

    assert solid.Volume() > windowed.Volume()


def test_display_window_negative_clearance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="display_window_clearance_mm",
    ):
        BoardDisplayEnclosureParameters(
            display_window_clearance_mm=-0.1,
        ).validate()


@pytest.mark.parametrize(
    "product",
    [
        "PICO2_OLED",
        "XIAO_ESP32S3_OLED",
    ],
)
def test_fit_analysis_accepts_generated_display_window(
    product: str,
) -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": product,
        }
    )

    build = build_board_display_enclosure_result(design)
    report = analyze_board_display_enclosure_fit(build)

    assert not any(
        finding.second_identifier == "display_window" for finding in report.findings
    )


def test_fit_analysis_detects_disabled_display_window() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            display_window_enabled=False,
        ),
    )
    report = analyze_board_display_enclosure_fit(build)

    window_findings = [
        finding
        for finding in report.findings
        if finding.second_identifier == "display_window"
    ]

    assert len(window_findings) == 1
    assert window_findings[0].kind == "collision"
    assert window_findings[0].intersection_volume_mm3 > 0


def test_fit_analysis_detects_undersized_display_window() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    small_window_build = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            display_window_clearance_mm=0.0,
        ),
    )

    verification_build = replace(
        small_window_build,
        policy=replace(
            small_window_build.policy,
            display_window_clearance_mm=1.0,
        ),
    )

    report = analyze_board_display_enclosure_fit(verification_build)

    assert any(
        finding.second_identifier == "display_window"
        and finding.intersection_volume_mm3 > 0
        for finding in report.findings
    )


def test_fit_analysis_detects_shifted_display_window() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)

    shifted_lid = build.parts["lid"].translate(
        (
            3.0,
            0.0,
            0.0,
        )
    )

    shifted_build = replace(
        build,
        parts={
            **build.parts,
            "lid": shifted_lid,
        },
    )

    report = analyze_board_display_enclosure_fit(shifted_build)

    assert any(
        finding.second_identifier == "display_window"
        and finding.intersection_volume_mm3 > 0
        for finding in report.findings
    )
