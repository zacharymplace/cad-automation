"""Package a folder of designs as a gift bundle for the person printing them.

`build_bundle` regenerates every design in a folder, then assembles a
self-contained directory (and zip) with the STL and STEP files, the
JSON design sources, and a printed guide addressed to the recipient:
what each part is, how big it is, how to print it, and how to remix
it. The guide's numbers come from the export metadata, so it never
drifts from the files beside it.
"""

import json
import shutil
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from zcad.bundle_manifest import verify_bundle, write_manifest

PRINT_NOTES: dict[tuple[str, str], str] = {
    ("pixel_heart_planter", "planter"): (
        "Floor down, no supports, 3 perimeters. Slow the outer wall a "
        "touch so the 1 mm grooves stay crisp."
    ),
    ("pixel_heart_planter", "saucer"): (
        "Flat, text up, no supports. Add a colour change at 3.0 mm in "
        "PrusaSlicer (the + on the layer slider): lip, ribs and text come "
        "out in the second colour."
    ),
    ("pixel_garden_module", "main"): (
        "Cup up, no supports. Print two first and check they slide "
        "together; tune rail_clearance before printing the rest."
    ),
    ("pixel_plant_marker", "main"): (
        "Flat on its back, text up, no supports. A whole set fits on one plate."
    ),
    ("pixel_coaster", "main"): (
        "Flat, no supports. Colour change at 3.8 mm on the layer slider and "
        "the pad and rim print in a second colour."
    ),
    ("pixel_block_planter", "main"): (
        "Cup up, no supports, 3 perimeters. The face is recessed into the "
        "front wall; a marker in the recess makes it pop."
    ),
    ("pixel_ring_dish", "main"): (
        "Flat, no supports. The cone tapers gently and prints unaided."
    ),
    ("pixel_photo_stand", "main"): (
        "Flat, no supports. The slot leans back 12 degrees so a 4x6 photo "
        "rests instead of flopping."
    ),
    ("pixel_hook", "main"): (
        "On its side, profile flat on the bed, no supports. Mount with two "
        "4 mm countersunk screws or a strong adhesive strip."
    ),
}

REMIX_KNOBS: dict[str, str] = {
    "pixel_heart_planter": (
        "`pattern` (any pixel shape), `label` / `subtitle`, `pixel_size`, "
        "`height_pixels`, `clearance`"
    ),
    "pixel_garden_module": "`size`, `height`, `rail_clearance`, `drain_hole_diameter`",
    "pixel_plant_marker": "`label`, `pattern`, `stake_length`",
    "pixel_coaster": "`pattern` (islands allowed), `pixel_size`, `size`",
    "pixel_block_planter": (
        "`front_pattern`, `side_pattern`, `face_pixels`, `pixel_size`"
    ),
    "pixel_ring_dish": "`pattern`, `cone_pixel`, `cone_height`, `rim_height`",
    "pixel_hook": "`pattern`, `width`, `arm_length`, `lip_height`",
    "pixel_photo_stand": "`pattern`, `slot_width`, `slot_tilt_degrees`, `height`",
}


@dataclass(frozen=True)
class BundledPart:
    """One exported part and the files that describe it."""

    design_name: str
    design_type: str
    part_name: str
    stl_path: Path
    step_path: Path
    metadata_path: Path
    bounds_mm: tuple[float, float, float]
    mass_g: float | None

    @property
    def label(self) -> str:
        if self.part_name == "main":
            return self.design_name
        return f"{self.design_name} ({self.part_name})"


def read_design_names(design_dir: Path) -> list[tuple[Path, str, str]]:
    """`(path, name, type)` for every design JSON in the folder."""
    designs = []

    for path in sorted(design_dir.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            design = json.load(handle)

        designs.append((path, design["name"], design["type"]))

    return designs


def collect_parts(
    exports_dir: Path,
    design_names: set[str],
) -> list[BundledPart]:
    """Find exported parts for the given designs via their metadata."""
    parts = []

    for metadata_path in sorted(exports_dir.glob("*.metadata.json")):
        with metadata_path.open(encoding="utf-8") as handle:
            metadata = json.load(handle)

        design = metadata.get("design", {})

        if design.get("name") not in design_names:
            continue

        stem = metadata_path.name.removesuffix(".metadata.json")
        stl_path = exports_dir / f"{stem}.stl"
        step_path = exports_dir / f"{stem}.step"

        for required in (stl_path, step_path):
            if not required.is_file():
                raise FileNotFoundError(
                    f"Export is missing beside metadata: {required}"
                )

        part = metadata["part"]
        box = part["bounding_box_mm"]

        parts.append(
            BundledPart(
                design_name=design["name"],
                design_type=design["type"],
                part_name=part["name"],
                stl_path=stl_path,
                step_path=step_path,
                metadata_path=metadata_path,
                bounds_mm=(box["x"], box["y"], box["z"]),
                mass_g=part.get("estimated_mass_g"),
            )
        )

    return parts


def write_guide(
    path: Path,
    *,
    title: str,
    recipient: str,
    parts: list[BundledPart],
    designs: list[tuple[Path, str, str]],
    printer_name: str = "your printer",
) -> None:
    """Describe bundled parts without claiming unrecorded validation."""
    lines = [
        f"# {title}",
        "",
        f"{recipient},",
        "",
        "A parametric pixel-family gift: STL files for slicing, STEP files",
        "for CAD, and the JSON designs for making these parts your own.",
        "",
        "## Before printing",
        "",
        f"Intended printer: {printer_name}.",
        "This guide does not verify printer fit, minimum wall thickness,",
        "support requirements, or successful physical printing.",
        "Review orientation, dimensions, and toolpaths in your slicer.",
        "Print mating parts as a small fit trial before making a full set.",
        "",
        "## What's in here",
        "",
        "Dimensions and mass estimates below are copied from export metadata.",
        "Mass estimates are not slicer filament-use estimates.",
        "Print suggestions are unverified starting points; check them against",
        "the actual design parameters and slicer preview.",
        "",
        "| Part | Size (mm) | Estimated mass | Suggested print setup (unverified) |",
        "| --- | --- | --- | --- |",
    ]

    for part in parts:
        x, y, z = part.bounds_mm
        mass = f"~{part.mass_g:.0f} g" if part.mass_g is not None else "n/a"
        notes = PRINT_NOTES.get(
            (part.design_type, part.part_name),
            "No product-specific suggestion recorded; review in your slicer.",
        )
        lines.append(
            f"| `{part.label}` | {x:.0f} × {y:.0f} × {z:.0f} | {mass} | {notes} |"
        )

    lines += [
        "",
        "## Files and remixing",
        "",
        "- `stl/`: exported meshes for slicing.",
        "- `step/`: exported CAD geometry.",
        "- `designs/`: supplied JSON design sources.",
        "",
        "Inspect each JSON for its actual parameters and clearances.",
        "Rebuild changed designs before slicing again.",
        "",
        "| Design | Type | Knobs worth turning |",
        "| --- | --- | --- |",
    ]
    for design_path, _name, design_type in designs:
        knobs = REMIX_KNOBS.get(design_type, "see the JSON")
        lines.append(f"| `{design_path.name}` | `{design_type}` | {knobs} |")

    lines += [
        "",
        "Rebuild with `zcad` from the cad-automation environment:",
        "",
        "```bash",
        "zcad designs/<design>.json",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _cli_builder(
    printer_profile: Path | None,
) -> Callable[[Path, Path], tuple[str, ...]]:
    """Build one design through the zcad CLI into `exports_dir`."""
    from zcad.cli import run

    def build(path: Path, exports_dir: Path) -> tuple[str, ...]:
        arguments = [str(path), "--output", str(exports_dir)]

        if printer_profile is not None:
            arguments += ["--printer-profile", str(printer_profile)]

        expected = run(arguments)
        if expected is None:
            raise ValueError("Design builder did not report expected parts")
        return expected

    return build


def build_bundle(
    *,
    design_dir: Path,
    exports_dir: Path,
    output_dir: Path,
    bundle_name: str,
    title: str,
    recipient: str,
    build: bool = True,
    guide_html: Path | None = None,
    build_design: Callable[[Path, Path], tuple[str, ...]] | None = None,
    printer_profile: Path | None = None,
    printer_name: str = "your printer",
) -> Path:
    """Stage, verify, then publish a folder and ZIP with exception rollback.

    Builders receive (design_path, fresh_export_directory) and return part names
    captured from the generated assembly before export. Existing exports
    are read only with build=False; that mode does not establish freshness.
    Failed stages are retained for diagnosis/recovery. Publication is not
    crash-atomic across the two output paths.
    """
    if (
        not bundle_name
        or bundle_name in {".", ".."}
        or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
            for c in bundle_name
        )
    ):
        raise ValueError("bundle_name must be a single safe filename")
    designs = read_design_names(design_dir)

    if not designs:
        raise ValueError(f"No design JSON files found in {design_dir}")

    names = [name for _path, name, _type in designs]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate design names")
    bundle_dir = output_dir / bundle_name
    zip_path = output_dir / f"{bundle_name}.zip"
    inputs = [design_dir, exports_dir, guide_html, printer_profile]
    for target in (bundle_dir, zip_path):
        if target.is_symlink():
            raise ValueError(f"Output cannot be a symlink: {target}")
        for item in inputs:
            if item is not None and (
                item.resolve() == target.resolve()
                or target.resolve() in item.resolve().parents
            ):
                raise ValueError(f"Output overlaps input: {target}")
    if bundle_dir.exists() and not bundle_dir.is_dir():
        raise ValueError("Bundle output must be a directory")
    if zip_path.exists() and not zip_path.is_file():
        raise ValueError("ZIP output must be a file")
    output_dir.mkdir(parents=True, exist_ok=True)
    lock = output_dir / f".{bundle_name}.lock"
    lock.mkdir()  # Refuse concurrent publication to the same bundle name.
    stage = None
    try:
        stage = Path(tempfile.mkdtemp(prefix=f".{bundle_name}-stage-", dir=output_dir))
        staged_bundle = stage / bundle_name
        for folder in ("stl", "step", "designs", "metadata"):
            (staged_bundle / folder).mkdir(parents=True)
        parts = []
        staged_designs = []
        manifest_designs = []
        builder = (build_design or _cli_builder(printer_profile)) if build else None
        for index, (design_path, name, design_type) in enumerate(designs):
            copied = staged_bundle / "designs" / design_path.name
            shutil.copy2(design_path, copied)
            staged_designs.append((copied, name, design_type))
            current_exports = exports_dir
            expected_parts = None
            if build:
                current_exports = stage / f"exports-{index}"
                current_exports.mkdir()
                expected_parts = builder(copied, current_exports)
                if (
                    not isinstance(expected_parts, tuple)
                    or not expected_parts
                    or any(not isinstance(n, str) or not n for n in expected_parts)
                    or len(set(expected_parts)) != len(expected_parts)
                ):
                    raise ValueError("Builder must return unique expected part names")
            current_parts = collect_parts(current_exports, {name})
            if not current_parts:
                raise FileNotFoundError(f"No exports found for designs: {name}")
            actual_parts = [part.part_name for part in current_parts]
            if len(set(actual_parts)) != len(actual_parts):
                raise ValueError(f"Duplicate exported part names for {name}")
            if build and set(actual_parts) != set(expected_parts):
                raise ValueError(
                    f"Incomplete or unexpected exports for {name}: "
                    f"expected {sorted(expected_parts)}, got {sorted(actual_parts)}"
                )
            part_records = []
            for part in current_parts:
                if part.design_type != design_type:
                    raise ValueError(f"Export type mismatch for {name}")
                for source, folder in (
                    (part.stl_path, "stl"),
                    (part.step_path, "step"),
                    (part.metadata_path, "metadata"),
                ):
                    destination = staged_bundle / folder / source.name
                    if destination.exists():
                        raise ValueError(f"Export filename collision: {source.name}")
                    shutil.copy2(source, destination)
                record = {
                    "name": part.part_name,
                    "stl": f"stl/{part.stl_path.name}",
                    "step": f"step/{part.step_path.name}",
                    "metadata": f"metadata/{part.metadata_path.name}",
                }
                metadata_path = staged_bundle / record["metadata"]
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                metadata["outputs"] = {"step": record["step"], "stl": record["stl"]}
                metadata["bundle_output_path_base"] = "bundle_root"
                metadata_path.write_text(
                    json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
                )
                part_records.append(record)
            manifest_designs.append(
                {
                    "name": name,
                    "type": design_type,
                    "source": f"designs/{copied.name}",
                    "expected_parts": list(expected_parts) if build else None,
                    "parts": part_records,
                }
            )
            parts.extend(current_parts)
        write_guide(
            staged_bundle / "README.md",
            title=title,
            recipient=recipient,
            parts=parts,
            designs=staged_designs,
            printer_name=printer_name,
        )
        with (staged_bundle / "README.md").open("a", encoding="utf-8") as handle:
            handle.write("\nExport metadata is included in `metadata/`.\n")
            handle.write(
                "Metadata output paths are relative to the bundle root.\n"
                "`bundle-manifest.json` records design and artifact hashes.\n"
                "Verify with `zcad bundle-verify <bundle-directory>`.\n"
                "The manifest does not attest implementation source or physical fit.\n"
            )
            if not build:
                handle.write("Existing exports reused; freshness is unverified.\n")
        if guide_html is not None:
            shutil.copy2(guide_html, staged_bundle / "guide.html")
        write_manifest(staged_bundle, manifest_designs, fresh=build)
        verify_bundle(staged_bundle)
        staged_zip = Path(
            shutil.make_archive(
                str(stage / bundle_name),
                "zip",
                stage,
                bundle_name,
            )
        )
        with zipfile.ZipFile(staged_zip) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP integrity check failed")
            expected = {
                str(p.relative_to(stage)): p
                for p in staged_bundle.rglob("*")
                if p.is_file()
            }
            actual = {i.filename for i in archive.infolist() if not i.is_dir()}
            if actual != set(expected):
                raise ValueError("ZIP contents differ from staged bundle")
            for name, path in expected.items():
                if archive.read(name) != path.read_bytes():
                    raise ValueError(f"ZIP bytes differ: {name}")
        backups = []
        installed = []
        try:
            for target, candidate in (
                (bundle_dir, staged_bundle),
                (zip_path, staged_zip),
            ):
                if target.exists():
                    backup = stage / f"previous-{target.name}"
                    target.rename(backup)
                    backups.append((target, backup))
                candidate.rename(target)
                installed.append(target)
        except BaseException:
            for target in reversed(installed):
                target.rename(stage / f"failed-{target.name}")
            for target, backup in reversed(backups):
                backup.rename(target)
            raise
    except BaseException as error:
        error.add_note(f"Bundle staging/recovery directory retained: {stage}")
        raise
    finally:
        lock.rmdir()
    shutil.rmtree(stage)
    return bundle_dir
