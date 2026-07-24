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
