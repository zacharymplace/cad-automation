"""Tests for registry-driven board-display JSON designs."""

import json

import pytest

from zcad.assemblies.pico2_oled import (
    Pico2OledAssemblyParameters,
)
from zcad.assemblies.xiao_esp32s3_oled import (
    XiaoEsp32S3OledAssemblyParameters,
)
from zcad.designs import (
    BoardDisplayDesign,
    build_board_display_design,
    load_board_display_design,
    parse_board_display_design,
)


def test_parse_design_uses_registered_product_defaults() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    assert design.schema_version == "1"
    assert design.product == "PICO2_OLED"
    assert isinstance(
        design.parameters,
        Pico2OledAssemblyParameters,
    )
    assert design.parameters.display_y_mm == pytest.approx(6.0)


def test_parse_design_merges_partial_parameter_overrides() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
            "parameters": {
                "display_z_mm": 10,
                "usb_access_clearance_mm": 3.5,
            },
        }
    )

    assert isinstance(
        design.parameters,
        XiaoEsp32S3OledAssemblyParameters,
    )
    assert design.parameters.display_y_mm == pytest.approx(-6.0)
    assert design.parameters.display_z_mm == pytest.approx(10.0)
    assert design.parameters.usb_access_clearance_mm == pytest.approx(3.5)


def test_build_design_resolves_product_through_registry() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
            "parameters": {
                "board_x_mm": 2.0,
            },
        }
    )

    assembly = build_board_display_design(design)

    assert (
        assembly.get("board").metadata["hardware_identifier"] == "SEEED_XIAO_ESP32_S3"
    )
    assert assembly.get("board").placement.x_mm == pytest.approx(2.0)


def test_load_design_reads_json_file(tmp_path) -> None:
    path = tmp_path / "design.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "product": "PICO2_OLED",
                "parameters": {
                    "display_z_mm": 9.0,
                },
            }
        ),
        encoding="utf-8",
    )

    design = load_board_display_design(path)

    assert design.product == "PICO2_OLED"
    assert design.parameters.display_y_mm == pytest.approx(6.0)
    assert design.parameters.display_z_mm == pytest.approx(9.0)


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ([], "design must be a JSON object"),
        (
            {
                "schema_version": "2",
                "product": "PICO2_OLED",
            },
            "schema_version",
        ),
        (
            {
                "schema_version": "1",
                "product": "",
            },
            "product must not be empty",
        ),
        (
            {
                "schema_version": "1",
                "product": "PICO2_OLED",
                "unexpected": True,
            },
            "unknown design field",
        ),
        (
            {
                "schema_version": "1",
                "product": "PICO2_OLED",
                "parameters": [],
            },
            "parameters must be a JSON object",
        ),
        (
            {
                "schema_version": "1",
                "product": "PICO2_OLED",
                "parameters": {
                    "unknown_mm": 1.0,
                },
            },
            "unknown parameter field",
        ),
        (
            {
                "schema_version": "1",
                "product": "PICO2_OLED",
                "parameters": {
                    "display_z_mm": True,
                },
            },
            "display_z_mm must be a number",
        ),
        (
            {
                "schema_version": "1",
                "product": "PICO2_OLED",
                "parameters": {
                    "board_z_mm": -0.1,
                },
            },
            "board_z_mm",
        ),
    ],
)
def test_parse_design_rejects_invalid_documents(
    document: object,
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        parse_board_display_design(document)


def test_parse_design_rejects_unknown_product() -> None:
    with pytest.raises(
        KeyError,
        match="unknown board-display product identifier",
    ):
        parse_board_display_design(
            {
                "schema_version": "1",
                "product": "UNKNOWN_PRODUCT",
            }
        )


def test_load_design_rejects_invalid_json(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(
        '{"schema_version":',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="invalid JSON design",
    ):
        load_board_display_design(path)


def test_build_revalidates_schema_version() -> None:
    design = BoardDisplayDesign(
        schema_version="2",
        product="PICO2_OLED",
        parameters=Pico2OledAssemblyParameters(),
    )

    with pytest.raises(
        ValueError,
        match="schema_version",
    ):
        build_board_display_design(design)
