"""Tests for the gift bundle packager."""

import json
import zipfile
from pathlib import Path

import pytest

from zcad.bundle import build_bundle, collect_parts


def fake_export(
    exports: Path,
    *,
    design_name: str,
    design_type: str,
    part_name: str,
) -> None:
    stem = design_name if part_name == "main" else f"{design_name}-{part_name}"
    (exports / f"{stem}.stl").write_text("solid")
    (exports / f"{stem}.step").write_text("ISO-10303-21;")
    (exports / f"{stem}.metadata.json").write_text(
        json.dumps(
            {
                "design": {"name": design_name, "type": design_type},
                "part": {
                    "name": part_name,
                    "bounding_box_mm": {"x": 10.0, "y": 20.0, "z": 5.0},
                    "estimated_mass_g": 12.3,
                },
            }
        )
    )


def fake_design(designs: Path, name: str, design_type: str) -> None:
    (designs / f"{name}.json").write_text(
        json.dumps({"name": name, "type": design_type, "parameters": {}})
    )


@pytest.fixture
def workspace(tmp_path: Path) -> dict[str, Path]:
    designs = tmp_path / "designs"
    exports = tmp_path / "exports"
    designs.mkdir()
    exports.mkdir()

    fake_design(designs, "coaster", "pixel_coaster")
    fake_design(designs, "planter", "pixel_heart_planter")
    fake_export(
        exports, design_name="coaster", design_type="pixel_coaster", part_name="main"
    )
    fake_export(
        exports,
        design_name="planter",
        design_type="pixel_heart_planter",
        part_name="planter",
    )
    fake_export(
        exports,
        design_name="planter",
        design_type="pixel_heart_planter",
        part_name="saucer",
    )
    # An unrelated export that must not be swept into the bundle.
    fake_export(exports, design_name="tray", design_type="tray", part_name="main")

    return {"designs": designs, "exports": exports, "out": tmp_path / "dist"}


def test_collect_parts_matches_on_metadata_not_filename_prefix(
    workspace: dict[str, Path],
) -> None:
    parts = collect_parts(workspace["exports"], {"planter", "coaster"})

    assert [p.label for p in parts] == [
        "coaster",
        "planter (planter)",
        "planter (saucer)",
    ]


def test_build_bundle_assembles_folders_guide_and_zip(
    workspace: dict[str, Path],
) -> None:
    bundle = build_bundle(
        design_dir=workspace["designs"],
        exports_dir=workspace["exports"],
        output_dir=workspace["out"],
        bundle_name="starter-pack",
        title="Player 2 Starter Pack",
        recipient="Player 2",
        build=False,
    )

    assert sorted(p.name for p in (bundle / "stl").iterdir()) == [
        "coaster.stl",
        "planter-planter.stl",
        "planter-saucer.stl",
    ]
    assert sorted(p.name for p in (bundle / "designs").iterdir()) == [
        "coaster.json",
        "planter.json",
    ]

    guide = (bundle / "README.md").read_text()
    assert guide.startswith("# Player 2 Starter Pack")
    assert "Player 2," in guide
    assert "`planter (saucer)` | 10 × 20 × 5 | ~12 g" in guide
    assert "`tray`" not in guide

    with zipfile.ZipFile(workspace["out"] / "starter-pack.zip") as archive:
        names = archive.namelist()

    assert "starter-pack/README.md" in names
    assert "starter-pack/step/coaster.step" in names


def test_build_bundle_calls_builder_for_each_design(
    workspace: dict[str, Path],
) -> None:
    built: list[str] = []

    def builder(path: Path, exports: Path) -> tuple[str, ...]:
        built.append(path.name)
        design = json.loads(path.read_text())
        assert not list(exports.iterdir())
        fake_export(
            exports,
            design_name=design["name"],
            design_type=design["type"],
            part_name="main",
        )
        return ("main",)

    build_bundle(
        design_dir=workspace["designs"],
        exports_dir=workspace["exports"],
        output_dir=workspace["out"],
        bundle_name="starter-pack",
        title="T",
        recipient="R",
        build=True,
        build_design=builder,
    )

    assert built == ["coaster.json", "planter.json"]


def test_build_bundle_reports_missing_exports(workspace: dict[str, Path]) -> None:
    fake_design(workspace["designs"], "ghost", "pixel_coaster")

    with pytest.raises(FileNotFoundError, match="ghost"):
        build_bundle(
            design_dir=workspace["designs"],
            exports_dir=workspace["exports"],
            output_dir=workspace["out"],
            bundle_name="starter-pack",
            title="T",
            recipient="R",
            build=False,
        )


def test_bundle_guide_does_not_invent_validation_or_contents(
    workspace: dict[str, Path],
) -> None:
    bundle = build_bundle(
        design_dir=workspace["designs"],
        exports_dir=workspace["exports"],
        output_dir=workspace["out"],
        bundle_name="honest-guide",
        title="Gift",
        recipient="Player 2",
        build=False,
    )
    guide = (bundle / "README.md").read_text()

    assert "`planter (saucer)` | 10 × 20 × 5 | ~12 g" in guide
    assert "Suggested print setup (unverified)" in guide
    assert "This guide does not verify printer fit" in guide
    for unsupported in (
        "Every part was generated as a valid solid",
        "Nothing needs supports",
        "Everything fits the bed",
        "135 mm",
        "prusa-mk4.json",
        "guide.html",
        "cake topper",
        "0.25 mm",
        "0.5 mm",
    ):
        assert unsupported not in guide
