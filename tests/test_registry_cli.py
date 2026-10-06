"""Registry-driven CLI behavior tests."""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    """Run the ZCAD CLI in a subprocess."""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "src"

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "zcad.cli",
            *arguments,
        ],
        cwd=Path.cwd(),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def write_design(
    path: Path,
    *,
    product: str = "PICO2_OLED",
) -> None:
    """Write a minimal registry-driven design."""
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "product": product,
                "parameters": {
                    "display_z_mm": 9.0,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_products_lists_registered_products() -> None:
    result = run_cli("products")

    assert result.returncode == 0
    assert "PICO2_OLED" in result.stdout
    assert "XIAO_ESP32S3_OLED" in result.stdout
    assert "RASPBERRY_PI_PICO_2" in result.stdout
    assert "SEEED_XIAO_ESP32_S3" in result.stdout
    assert result.stderr == ""


def test_design_validate_reports_valid_design(
    tmp_path: Path,
) -> None:
    path = tmp_path / "design.json"
    write_design(path)

    result = run_cli(
        "design",
        "validate",
        str(path),
    )

    assert result.returncode == 0
    assert f"Valid design: {path}" in result.stdout
    assert "Schema version: 1" in result.stdout
    assert "Product: PICO2_OLED" in result.stdout
    assert result.stderr == ""


def test_design_inspect_reports_resolved_product(
    tmp_path: Path,
) -> None:
    path = tmp_path / "design.json"
    write_design(
        path,
        product="XIAO_ESP32S3_OLED",
    )

    result = run_cli(
        "design",
        "inspect",
        str(path),
    )

    assert result.returncode == 0
    assert "Product: XIAO_ESP32S3_OLED" in result.stdout
    assert "Board: SEEED_XIAO_ESP32_S3" in result.stdout
    assert "Display: REFERENCE_OLED_128X64" in result.stdout
    assert "display_y_mm: -6.0" in result.stdout
    assert "display_z_mm: 9.0" in result.stdout
    assert "  board" in result.stdout
    assert "  usb_connector" in result.stdout
    assert "  display" in result.stdout
    assert result.stderr == ""


def test_design_validate_rejects_unknown_product(
    tmp_path: Path,
) -> None:
    path = tmp_path / "design.json"
    write_design(
        path,
        product="UNKNOWN_PRODUCT",
    )

    result = run_cli(
        "design",
        "validate",
        str(path),
    )

    assert result.returncode == 1
    assert "unknown board-display product identifier" in result.stderr
    assert "Traceback" not in result.stderr


def test_design_rejects_unknown_command() -> None:
    result = run_cli(
        "design",
        "unknown",
    )

    assert result.returncode == 1
    assert "unknown design command: unknown" in result.stderr
    assert "Traceback" not in result.stderr


def test_checked_in_pico_example_validates() -> None:
    result = run_cli(
        "design",
        "validate",
        "designs/board-display/pico2-oled.example.json",
    )

    assert result.returncode == 0
    assert "Product: PICO2_OLED" in result.stdout
    assert result.stderr == ""


def test_checked_in_xiao_example_inspects() -> None:
    result = run_cli(
        "design",
        "inspect",
        "designs/board-display/xiao-esp32s3-oled.example.json",
    )

    assert result.returncode == 0
    assert "Product: XIAO_ESP32S3_OLED" in result.stdout
    assert "Board: SEEED_XIAO_ESP32_S3" in result.stdout
    assert result.stderr == ""


def test_checked_in_pico_example_passes_analysis() -> None:
    result = run_cli(
        "design",
        "analyze",
        "designs/board-display/pico2-oled.example.json",
    )

    assert result.returncode == 0
    assert "Finding count: 0" in result.stdout
    assert "Analysis passed" in result.stdout
    assert result.stderr == ""


def test_design_analyze_reports_interference(
    tmp_path: Path,
) -> None:
    path = tmp_path / "interfering.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "product": "PICO2_OLED",
                "parameters": {"display_y_mm": 0.0, "display_z_mm": 3.0},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_cli(
        "design",
        "analyze",
        str(path),
    )

    assert result.returncode == 1
    assert "Finding count:" in result.stdout
    assert "Kind:" in result.stdout
    assert "board-display design analysis found" in result.stderr
    assert "Traceback" not in result.stderr


def test_checked_in_pico_example_builds_and_exports(
    tmp_path: Path,
) -> None:
    output = tmp_path / "exports"

    result = run_cli(
        "design",
        "build",
        "designs/board-display/pico2-oled.example.json",
        "--output",
        str(output),
    )

    assert result.returncode == 0
    assert "Generated: pico2-oled" in result.stdout
    assert "Part count: 2" in result.stdout
    assert "Part: body" in result.stdout
    assert "Part: lid" in result.stdout
    assert "STEP:" in result.stdout
    assert "STL:" in result.stdout
    assert "META:" in result.stdout
    assert result.stderr == ""

    assert list(output.rglob("*.step"))
    assert list(output.rglob("*.stl"))
    assert list(output.rglob("*.json"))


def test_checked_in_xiao_example_builds_and_exports(
    tmp_path: Path,
) -> None:
    output = tmp_path / "exports"

    result = run_cli(
        "design",
        "build",
        "designs/board-display/xiao-esp32s3-oled.example.json",
        "--output",
        str(output),
    )

    assert result.returncode == 0
    assert "Generated: xiao-esp32s3-oled" in result.stdout
    assert "Part count: 2" in result.stdout
    assert result.stderr == ""


def test_design_build_rejects_unknown_product(
    tmp_path: Path,
) -> None:
    path = tmp_path / "unknown.json"
    write_design(
        path,
        product="UNKNOWN_PRODUCT",
    )

    result = run_cli(
        "design",
        "build",
        str(path),
        "--output",
        str(tmp_path / "exports"),
    )

    assert result.returncode == 1
    assert "unknown board-display product identifier" in result.stderr
    assert "Traceback" not in result.stderr


def test_checked_in_pico_example_passes_fit_verification() -> None:
    result = run_cli(
        "design",
        "verify-fit",
        "designs/board-display/pico2-oled.example.json",
    )

    assert result.returncode == 0
    assert "Product: PICO2_OLED" in result.stdout
    assert "Finding count: 0" in result.stdout
    assert "Fit verification passed" in result.stdout
    assert result.stderr == ""


def test_checked_in_xiao_example_passes_fit_verification() -> None:
    result = run_cli(
        "design",
        "verify-fit",
        "designs/board-display/xiao-esp32s3-oled.example.json",
    )

    assert result.returncode == 0
    assert "Product: XIAO_ESP32S3_OLED" in result.stdout
    assert "Finding count: 0" in result.stdout
    assert "Fit verification passed" in result.stdout
    assert result.stderr == ""


def test_verify_fit_rejects_unknown_product(
    tmp_path: Path,
) -> None:
    path = tmp_path / "unknown.json"
    write_design(
        path,
        product="UNKNOWN_PRODUCT",
    )

    result = run_cli(
        "design",
        "verify-fit",
        str(path),
    )

    assert result.returncode == 1
    assert "unknown board-display product identifier" in result.stderr
    assert "Traceback" not in result.stderr


def test_design_inspect_reports_custom_display_and_source(tmp_path):
    path = tmp_path / "custom.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "product": "PICO2_OLED",
                "display": {
                    "identifier": "SYNTHETIC_MODULE",
                    "module_width_mm": 30,
                    "module_height_mm": 25,
                    "module_depth_mm": 5,
                    "active_width_mm": 22,
                    "active_height_mm": 11,
                    "geometry_source": "synthetic fixture",
                },
            }
        )
    )
    result = run_cli("design", "inspect", str(path))
    assert result.returncode == 0, result.stderr
    assert "Display: SYNTHETIC_MODULE" in result.stdout
    assert "Display module: 30 × 25 × 5 mm" in result.stdout
    assert "Display geometry source: synthetic fixture" in result.stdout
    assert "Display geometry evidence: reference" in result.stdout
