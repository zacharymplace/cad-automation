"""Tests for the XIAO ESP32-S3 and OLED assembly."""

import pytest

from zcad.assemblies import (
    XiaoEsp32S3OledAssemblyParameters,
    analyze_xiao_esp32s3_oled_assembly,
    build_xiao_esp32s3_oled_assembly,
)


def test_xiao_assembly_uses_selected_hardware() -> None:
    assembly = build_xiao_esp32s3_oled_assembly()

    assert assembly.identifiers == (
        "board",
        "usb_connector",
        "display",
    )

    assert (
        assembly.get("board").metadata["hardware_identifier"] == "SEEED_XIAO_ESP32_S3"
    )
    assert assembly.get("usb_connector").metadata["hardware_identifier"] == "USB_C"


def test_xiao_connector_uses_positive_y_edge() -> None:
    assembly = build_xiao_esp32s3_oled_assembly()
    connector = assembly.get("usb_connector")

    assert connector.metadata["board_edge"] == "positive_y"
    assert connector.placement.x_mm == pytest.approx(0.0)
    assert connector.placement.y_mm == pytest.approx(7.0)


def test_xiao_connector_carries_positive_y_access_envelope() -> None:
    assembly = build_xiao_esp32s3_oled_assembly(
        XiaoEsp32S3OledAssemblyParameters(
            usb_access_clearance_mm=2.5,
        )
    )

    envelope = assembly.get("usb_connector").clearance_envelope

    assert envelope.positive_y_mm == pytest.approx(2.5)
    assert envelope.negative_y_mm == pytest.approx(0.0)


def test_xiao_default_assembly_passes_analysis() -> None:
    report = analyze_xiao_esp32s3_oled_assembly(build_xiao_esp32s3_oled_assembly())

    assert not report.has_findings


def test_xiao_negative_clearance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="usb_access_clearance_mm",
    ):
        build_xiao_esp32s3_oled_assembly(
            XiaoEsp32S3OledAssemblyParameters(
                usb_access_clearance_mm=-0.1,
            )
        )
