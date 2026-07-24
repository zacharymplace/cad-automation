"""Generate CAD models from JSON specifications."""

import argparse
import json
from pathlib import Path
from typing import Any

import cadquery as cq
from zcad_core.exporters import (
    ExportRequest,
    export_parts,
)
from zcad_core.profiles.loading import (
    load_material_profile,
    load_printer_profile,
)
from zcad_core.validation.profile_rules import (
    raise_for_validation_errors,
    validate_design_and_parts,
)

from zcad.generators.calibration.display_window_coupon import (
    DisplayWindowCouponParameters,
    build_display_window_coupon,
)
from zcad.generators.calibration.insert_boss_coupon import (
    InsertBossCouponParameters,
    build_insert_boss_coupon,
)
from zcad.generators.calibration.pico2_enclosure_fit import (
    Pico2EnclosureFitParameters,
    build_pico2_enclosure_fit,
)
from zcad.generators.calibration.pico2_mount_coupon import (
    Pico2MountCouponParameters,
    build_pico2_mount_coupon,
)
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

    if design_type == "display_window_coupon":
        return {
            "main": build_display_window_coupon(
                DisplayWindowCouponParameters(**raw_parameters)
            )
        }

    if design_type == "insert_boss_coupon":
        return {
            "main": build_insert_boss_coupon(
                InsertBossCouponParameters(**raw_parameters)
            )
        }

    if design_type == "pico2_enclosure_fit":
        return build_pico2_enclosure_fit(Pico2EnclosureFitParameters(**raw_parameters))

    if design_type == "pico2_mount_coupon":
        return {
            "main": build_pico2_mount_coupon(
                Pico2MountCouponParameters(**raw_parameters)
            )
        }

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

    result = export_parts(
        ExportRequest(
            design_name=design["name"],
            design_type=design["type"],
            parts=parts,
            output_directory=args.output,
            printer_profile=printer_profile,
            material_profile=material_profile,
            repository_root=Path.cwd(),
        )
    )

    print(f"Generated: {result.design_name}")
    print(f"Part count: {len(result.parts)}")

    for part in result.parts:
        bounds_x, bounds_y, bounds_z = part.bounds_mm

        print()
        print(f"Part: {part.part_name}")
        print("Valid solid: True")
        print(f"Volume: {part.volume_mm3:.2f} mm^3")
        print(f"Bounds: {bounds_x:.2f} × {bounds_y:.2f} × {bounds_z:.2f} mm")
        print(f"STEP: {part.step_path}")
        print(f"STL:  {part.stl_path}")
        print(f"META: {part.metadata_path}")


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
