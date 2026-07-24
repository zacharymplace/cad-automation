from pathlib import Path

from zcad.cli import (
    generate_parts,
    read_design,
)


def test_cli_generates_pico2_enclosure() -> None:
    design = read_design(Path("designs/calibration/pico2-enclosure-fit.json"))

    parts = generate_parts(design)

    assert parts["main"].val().isValid()
