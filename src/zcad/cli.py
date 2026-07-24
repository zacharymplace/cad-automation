"""Generate CAD models from JSON specifications."""

import argparse
import json
from pathlib import Path
from typing import Any

import cadquery as cq

from zcad.generators.enclosure import (
    EnclosureParameters,
    build_enclosure,
)
from zcad.generators.fit_coupon import (
    FitCouponParameters,
    build_fit_coupon,
)
from zcad.generators.gridfinity.bin import (
    GridfinityBinParameters,
    build_gridfinity_bin,
)
from zcad.generators.gridfinity.fit_coupon import (
    GridfinityFitCouponParameters,
    build_gridfinity_fit_coupon,
)
from zcad.generators.tolerance_coupon import (
    ToleranceCouponParameters,
    build_tolerance_coupon,
)
from zcad.generators.tray import (
    TrayParameters,
    build_tray,
)
from zcad.metadata.build_record import build_part_record
from zcad.profiles.loading import (
    load_material_profile,
    load_printer_profile,
)
from zcad.validation.profile_rules import (
    raise_for_validation_errors,
    validate_design_and_parts,
)

ModelParts = dict[str, cq.Workplane]


def read_design(
    path: Path,
) -> dict[str, Any]:
    """Read a design specification."""
    if not path.is_file():
        raise FileNotFoundError(f"Design file does not exist: {path}")

    with path.open(
        encoding="utf-8",
    ) as handle:
        design = json.load(handle)

    required = {
        "name",
        "type",
        "parameters",
    }

    missing = required.difference(design)

    if missing:
        raise ValueError(
            "Design is missing required fields: " + ", ".join(sorted(missing))
        )

    if not isinstance(
        design["parameters"],
        dict,
    ):
        raise ValueError("parameters must be a JSON object")

    return design


def generate_parts(
    design: dict[str, Any],
) -> ModelParts:
    """Generate one or more named model parts."""
    design_type = design["type"]
    raw_parameters = design["parameters"]

    if design_type == "tray":
        return {"main": build_tray(TrayParameters(**raw_parameters))}

    if design_type == "tolerance_coupon":
        return {
            "main": build_tolerance_coupon(ToleranceCouponParameters(**raw_parameters))
        }

    if design_type == "fit_coupon":
        return {"main": build_fit_coupon(FitCouponParameters(**raw_parameters))}

    if design_type == "gridfinity_fit_coupon":
        return build_gridfinity_fit_coupon(
            GridfinityFitCouponParameters(**raw_parameters)
        )

    if design_type == "gridfinity_bin":
        return {"main": build_gridfinity_bin(GridfinityBinParameters(**raw_parameters))}

    if design_type == "enclosure":
        return build_enclosure(EnclosureParameters(**raw_parameters))

    raise ValueError(f"Unsupported design type: {design_type}")


def output_stem(
    design_name: str,
    part_name: str,
    part_count: int,
) -> str:
    """Determine a stable export filename."""
    if part_count == 1 and part_name == "main":
        return design_name

    return f"{design_name}-{part_name}"


def export_parts(
    *,
    design_name: str,
    design_type: str,
    parts: ModelParts,
    output_directory: Path,
    printer_profile: dict[str, Any] | None,
    material_profile: dict[str, Any] | None,
    repository_root: Path,
) -> None:
    """Validate and export every generated part."""
    if not parts:
        raise ValueError("Generator returned no parts")

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"Generated: {design_name}")
    print(f"Part count: {len(parts)}")

    for part_name, model in parts.items():
        solid = model.val()

        if not solid.isValid():
            raise ValueError(f"Part is invalid: {part_name}")

        bounds = solid.BoundingBox()
        stem = output_stem(
            design_name,
            part_name,
            len(parts),
        )

        step_path = output_directory / f"{stem}.step"
        stl_path = output_directory / f"{stem}.stl"

        cq.exporters.export(
            model,
            str(step_path),
        )
        cq.exporters.export(
            model,
            str(stl_path),
        )

        metadata_path = output_directory / f"{stem}.metadata.json"

        record = build_part_record(
            design_name=design_name,
            design_type=design_type,
            part_name=part_name,
            model=model,
            step_path=step_path,
            stl_path=stl_path,
            printer_profile=printer_profile,
            material_profile=material_profile,
            repository_root=repository_root,
        )

        with metadata_path.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                record,
                handle,
                indent=2,
            )
            handle.write("\n")

        print()
        print(f"Part: {part_name}")
        print(f"Valid solid: {solid.isValid()}")
        print(f"Volume: {solid.Volume():.2f} mm^3")
        print(f"Bounds: {bounds.xlen:.2f} × {bounds.ylen:.2f} × {bounds.zlen:.2f} mm")
        print(f"STEP: {step_path}")
        print(f"STL:  {stl_path}")
        print(f"META: {metadata_path}")


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description=("Generate parametric CAD models from JSON specifications.")
    )

    parser.add_argument(
        "design",
        type=Path,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("exports"),
    )

    parser.add_argument(
        "--printer-profile",
        type=Path,
        default=Path("profiles/printers/default-fdm.json"),
    )

    parser.add_argument(
        "--material-profile",
        type=Path,
        default=Path("profiles/materials/petg.json"),
    )

    return parser


def run() -> None:
    """Run one CAD generation command."""
    args = build_parser().parse_args()
    design = read_design(args.design)
    parts = generate_parts(design)

    printer_profile = load_printer_profile(args.printer_profile)
    material_profile = load_material_profile(args.material_profile)

    validation_issues = validate_design_and_parts(
        design_type=design["type"],
        parameters=design["parameters"],
        parts=parts,
        printer_profile=printer_profile,
    )

    for issue in validation_issues:
        print(f"{issue.severity.upper()}: [{issue.code}] {issue.message}")

    raise_for_validation_errors(validation_issues)

    export_parts(
        design_name=design["name"],
        design_type=design["type"],
        parts=parts,
        output_directory=args.output,
        printer_profile=printer_profile,
        material_profile=material_profile,
        repository_root=Path.cwd(),
    )


def main() -> None:
    """Run the CLI with clean error handling."""
    try:
        run()
    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise SystemExit(f"zcad: error: {error}") from None


if __name__ == "__main__":
    main()
