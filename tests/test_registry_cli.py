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
