"""Tests for registry-driven board-display enclosure geometry."""

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
