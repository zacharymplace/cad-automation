"""CLI tests for the Pico 2 enclosure assembly."""

from pathlib import Path

from zcad.cli import (
    generate_parts,
    read_design,
)


def test_cli_generates_body_and_lid() -> None:
    design = read_design(Path("designs/calibration/pico2-enclosure-fit.json"))

    parts = generate_parts(design)

    assert set(parts) == {
        "body",
        "lid",
    }
    assert parts["body"].val().isValid()
    assert parts["lid"].val().isValid()


def test_cli_generates_custom_display_from_json(tmp_path):
    import json

    source = read_design(Path("designs/calibration/pico2-enclosure-fit.json"))
    source["parameters"]["display"] = {
        "identifier": "SYNTHETIC_CLI_MODULE",
        "module_width_mm": 36,
        "module_height_mm": 32,
        "module_depth_mm": 7,
        "active_width_mm": 24,
        "active_height_mm": 12,
        "geometry_source": "synthetic CLI fixture",
    }
    path = tmp_path / "custom-pico.json"
    path.write_text(json.dumps(source))
    parts = generate_parts(read_design(path))
    assert parts["body"].val().BoundingBox().xlen > 40
    assert parts["body"].val().BoundingBox().zlen > 12
    assert all(part.val().isValid() for part in parts.values())
