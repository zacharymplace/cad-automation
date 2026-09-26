"""Generate CAD models from JSON specifications."""

import argparse
import json
import sys
from dataclasses import fields
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

from zcad.assemblies import (
    get_board_display_product,
    list_board_display_products,
)
from zcad.assemblies.board_display import (
    analyze_board_display_product,
)
from zcad.bundle import build_bundle
from zcad.bundle_manifest import verify_bundle
from zcad.designs import (
    build_board_display_design,
    load_board_display_design,
)
from zcad.generators.board_display_enclosure import (
    analyze_board_display_enclosure_fit,
    build_board_display_enclosure,
    build_board_display_enclosure_result,
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
from zcad.generators.drip_tray import (
    DripTrayParameters,
    build_drip_tray,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
    build_enclosure,
)
from zcad.generators.fit_coupon import (
    FitCouponParameters,
    build_fit_coupon,
)
from zcad.generators.garnish_caddy import (
    GarnishCaddyParameters,
    build_garnish_caddy,
)
from zcad.generators.gridfinity.bin import (
    GridfinityBinParameters,
    build_gridfinity_bin,
)
from zcad.generators.gridfinity.fit_coupon import (
    GridfinityFitCouponParameters,
    build_gridfinity_fit_coupon,
)
from zcad.generators.grip_stand import (
    GripStandParameters,
    build_grip_stand,
)
from zcad.generators.ink_cap_tray import (
    InkCapTrayParameters,
    build_ink_cap_tray,
)
from zcad.generators.insert_tray import (
    InsertTrayParameters,
    build_insert_tray,
)
from zcad.generators.jigger_rack import (
    JiggerRackParameters,
    build_jigger_rack,
)
from zcad.generators.phone_stand import (
    PhoneStandParameters,
    build_phone_stand,
)
from zcad.generators.pixel_block_planter import (
    PixelBlockPlanterParameters,
    build_pixel_block_planter,
)
from zcad.generators.pixel_coaster import (
    PixelCoasterParameters,
    build_pixel_coaster,
)
from zcad.generators.pixel_garden_module import (
    PixelGardenModuleParameters,
    build_pixel_garden_module,
)
from zcad.generators.pixel_heart_planter import (
    PixelHeartPlanterParameters,
    build_pixel_heart_planter,
)
from zcad.generators.pixel_hook import (
    PixelHookParameters,
    build_pixel_hook,
)
from zcad.generators.pixel_photo_stand import (
    PixelPhotoStandParameters,
    build_pixel_photo_stand,
)
from zcad.generators.pixel_plant_marker import (
    PixelPlantMarkerParameters,
    build_pixel_plant_marker,
)
from zcad.generators.pixel_ring_dish import (
    PixelRingDishParameters,
    build_pixel_ring_dish,
)
from zcad.generators.sponge_caddy import (
    SpongeCaddyParameters,
    build_sponge_caddy,
)
from zcad.generators.stencil_holder import (
    StencilHolderParameters,
    build_stencil_holder,
)
from zcad.generators.tolerance_coupon import (
    ToleranceCouponParameters,
    build_tolerance_coupon,
)
from zcad.generators.travel_case import (
    TravelCaseParameters,
    build_travel_case,
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

    if design_type == "drip_tray":
        return build_drip_tray(DripTrayParameters(**raw_parameters))

    if design_type == "sponge_caddy":
        return build_sponge_caddy(SpongeCaddyParameters(**raw_parameters))

    if design_type == "phone_stand":
        return build_phone_stand(PhoneStandParameters(**raw_parameters))

    if design_type == "pixel_heart_planter":
        return build_pixel_heart_planter(PixelHeartPlanterParameters(**raw_parameters))

    if design_type == "pixel_garden_module":
        return build_pixel_garden_module(PixelGardenModuleParameters(**raw_parameters))

    if design_type == "pixel_plant_marker":
        return build_pixel_plant_marker(PixelPlantMarkerParameters(**raw_parameters))

    if design_type == "pixel_block_planter":
        return build_pixel_block_planter(PixelBlockPlanterParameters(**raw_parameters))

    if design_type == "pixel_ring_dish":
        return build_pixel_ring_dish(PixelRingDishParameters(**raw_parameters))

    if design_type == "pixel_photo_stand":
        return build_pixel_photo_stand(PixelPhotoStandParameters(**raw_parameters))

    if design_type == "pixel_hook":
        return build_pixel_hook(PixelHookParameters(**raw_parameters))

    if design_type == "pixel_coaster":
        return build_pixel_coaster(PixelCoasterParameters(**raw_parameters))

    if design_type == "ink_cap_tray":
        return build_ink_cap_tray(InkCapTrayParameters(**raw_parameters))

    if design_type == "grip_stand":
        return {"main": build_grip_stand(GripStandParameters(**raw_parameters))}

    if design_type == "stencil_holder":
        return {"main": build_stencil_holder(StencilHolderParameters(**raw_parameters))}

    if design_type == "travel_case":
        return {"main": build_travel_case(TravelCaseParameters(**raw_parameters))}

    if design_type == "insert_tray":
        return {"main": build_insert_tray(InsertTrayParameters(**raw_parameters))}

    if design_type == "garnish_caddy":
        return {"main": build_garnish_caddy(GarnishCaddyParameters(**raw_parameters))}

    if design_type == "jigger_rack":
        return {"main": build_jigger_rack(JiggerRackParameters(**raw_parameters))}

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


def _run_products_command(arguments: list[str]) -> None:
    """List registered board-display products."""
    if arguments:
        raise ValueError("products does not accept arguments")

    for product in list_board_display_products():
        print(product.identifier)
        print(f"  Board: {product.board.identifier}")
        print(f"  Display: {product.display.identifier}")


def _read_design_command_path(
    arguments: list[str],
    *,
    command: str,
) -> Path:
    """Validate and return the path for a design subcommand."""
    if len(arguments) != 1:
        raise ValueError(f"design {command} requires exactly one JSON design path")

    return Path(arguments[0])


def _run_design_validate_command(
    arguments: list[str],
) -> None:
    """Validate a registry-driven board-display design."""
    path = _read_design_command_path(
        arguments,
        command="validate",
    )
    design = load_board_display_design(path)

    print(f"Valid design: {path}")
    print(f"Schema version: {design.schema_version}")
    print(f"Product: {design.product}")


def _run_design_analyze_command(
    arguments: list[str],
) -> None:
    """Analyze a registry-driven board-display design."""
    path = _read_design_command_path(
        arguments,
        command="analyze",
    )
    design = load_board_display_design(path)
    product = get_board_display_product(design.product)
    assembly = build_board_display_design(design)

    report = analyze_board_display_product(
        product,
        assembly,
        minimum_board_display_clearance_mm=(
            design.parameters.board_display_clearance_mm
        ),
    )

    print(f"Design: {path}")
    print(f"Product: {design.product}")
    print(f"Finding count: {len(report.findings)}")

    for finding in report.findings:
        print()
        print(f"Kind: {finding.kind}")
        print(f"First: {finding.first_identifier}")
        print(f"Second: {finding.second_identifier}")

        if finding.intersection_volume_mm3 is not None:
            print(f"Intersection volume: {finding.intersection_volume_mm3:.3f} mm^3")

        if finding.required_clearance_mm is not None:
            print(f"Required clearance: {finding.required_clearance_mm:.3f} mm")

        if finding.measured_clearance_mm is not None:
            print(f"Measured clearance: {finding.measured_clearance_mm:.3f} mm")

    if report.has_findings:
        raise ValueError(
            f"board-display design analysis found {len(report.findings)} finding(s)"
        )

    print("Analysis passed")


def _run_design_verify_fit_command(
    arguments: list[str],
) -> None:
    """Verify a registry-driven product against its enclosure cavity."""
    path = _read_design_command_path(
        arguments,
        command="verify-fit",
    )
    design = load_board_display_design(path)
    build = build_board_display_enclosure_result(design)
    report = analyze_board_display_enclosure_fit(build)

    print(f"Design: {path}")
    print(f"Product: {design.product}")
    print(f"Finding count: {len(report.findings)}")

    for finding in report.findings:
        print()
        print(f"Kind: {finding.kind}")
        print(f"First: {finding.first_identifier}")
        print(f"Second: {finding.second_identifier}")

        if finding.intersection_volume_mm3 is not None:
            print(f"Intersection volume: {finding.intersection_volume_mm3:.3f} mm^3")

        if finding.required_clearance_mm is not None:
            print(f"Required clearance: {finding.required_clearance_mm:.3f} mm")

        if finding.measured_clearance_mm is not None:
            print(f"Measured clearance: {finding.measured_clearance_mm:.3f} mm")

    if report.has_findings:
        raise ValueError(
            "board-display enclosure fit verification found "
            f"{len(report.findings)} finding(s)"
        )

    print("Fit verification passed")


def _build_design_command_parser() -> argparse.ArgumentParser:
    """Create the registry-driven design build parser."""
    parser = argparse.ArgumentParser(
        prog="zcad design build",
        description=("Build and export a registered board-display enclosure."),
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


def _run_design_build_command(
    arguments: list[str],
) -> None:
    """Build and export a registry-driven board-display enclosure."""
    args = _build_design_command_parser().parse_args(arguments)

    design = load_board_display_design(args.design)
    parts = build_board_display_enclosure(design)

    printer_profile = load_printer_profile(args.printer_profile)
    material_profile = load_material_profile(args.material_profile)

    validation_issues = validate_design_and_parts(
        design_type="board_display_enclosure",
        parameters={
            "schema_version": design.schema_version,
            "product": design.product,
        },
        parts=parts,
        printer_profile=printer_profile,
    )

    for issue in validation_issues:
        print(f"{issue.severity.upper()}: [{issue.code}] {issue.message}")

    raise_for_validation_errors(validation_issues)

    result = export_parts(
        ExportRequest(
            design_name=(design.product.lower().replace("_", "-")),
            design_type="board_display_enclosure",
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


def _run_design_inspect_command(
    arguments: list[str],
) -> None:
    """Inspect a registry-driven board-display design."""
    path = _read_design_command_path(
        arguments,
        command="inspect",
    )
    design = load_board_display_design(path)
    product = get_board_display_product(design.product)
    assembly = build_board_display_design(design)

    print(f"Design: {path}")
    print(f"Schema version: {design.schema_version}")
    print(f"Product: {design.product}")
    print(f"Board: {product.board.identifier}")
    print(f"Display: {product.display.identifier}")
    print("Parameters:")

    for field in fields(design.parameters):
        value = getattr(design.parameters, field.name)
        print(f"  {field.name}: {value}")

    print("Components:")

    for identifier in assembly.identifiers:
        print(f"  {identifier}")


def _run_design_command(arguments: list[str]) -> None:
    """Run one registry-driven design command."""
    if not arguments:
        raise ValueError(
            "design requires a command: "
            "validate, inspect, analyze, verify-fit, or build"
        )

    command, *remaining = arguments

    if command == "validate":
        _run_design_validate_command(remaining)
        return

    if command == "inspect":
        _run_design_inspect_command(remaining)
        return

    if command == "analyze":
        _run_design_analyze_command(remaining)
        return

    if command == "verify-fit":
        _run_design_verify_fit_command(remaining)
        return

    if command == "build":
        _run_design_build_command(remaining)
        return

    raise ValueError(f"unknown design command: {command}")


def _build_bundle_command_parser() -> argparse.ArgumentParser:
    """Create the gift-bundle parser."""
    parser = argparse.ArgumentParser(
        prog="zcad bundle",
        description=(
            "Build every design in a folder and package the exports, sources, "
            "and a recipient-facing guide as a folder plus zip."
        ),
    )
    parser.add_argument("design_dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument(
        "--exports", type=Path, default=Path("exports"),
        help="existing exports for --skip-build; fresh builds use isolated staging",
    )
    parser.add_argument("--name", default="starter-pack")
    parser.add_argument("--title", default="Starter Pack")
    parser.add_argument("--recipient", default="you")
    parser.add_argument("--guide-html", type=Path, default=None)
    parser.add_argument("--printer-profile", type=Path, default=None)
    parser.add_argument("--printer-name", default="your printer")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="package existing exports without regenerating them",
    )
    return parser


def _run_bundle_command(arguments: list[str]) -> None:
    """Package a folder of designs for the person printing them."""
    args = _build_bundle_command_parser().parse_args(arguments)

    bundle_dir = build_bundle(
        design_dir=args.design_dir,
        exports_dir=args.exports,
        output_dir=args.output,
        bundle_name=args.name,
        title=args.title,
        recipient=args.recipient,
        build=not args.skip_build,
        guide_html=args.guide_html,
        printer_profile=args.printer_profile,
        printer_name=args.printer_name,
    )

    print(f"Bundle: {bundle_dir}")
    print(f"Zip:    {bundle_dir.parent / (bundle_dir.name + '.zip')}")


def run(
    argv: list[str] | None = None,
) -> tuple[str, ...] | None:
    """Run one CAD or registry-driven design command."""
    arguments = list(argv) if argv is not None else sys.argv[1:]

    if arguments and arguments[0] == "garden-assembly":
        from zcad.generators.pixel_garden_assembly import run_garden_assembly

        run_garden_assembly(arguments[1:])
        return

    if arguments and arguments[0] == "bundle-verify":
        parser = argparse.ArgumentParser(prog="zcad bundle-verify")
        parser.add_argument("directory", type=Path)
        parser.add_argument("--manifest-sha256", default=None)
        verification = parser.parse_args(arguments[1:])
        print(json.dumps(verify_bundle(
            verification.directory,
            expected_manifest_sha256=verification.manifest_sha256,
        ), indent=2))
        return

    if arguments and arguments[0] == "products":
        _run_products_command(arguments[1:])
        return

    if arguments and arguments[0] == "bundle":
        _run_bundle_command(arguments[1:])
        return

    if arguments and arguments[0] == "design":
        _run_design_command(arguments[1:])
        return

    args = build_parser().parse_args(arguments)
    design = read_design(args.design)
    parts = generate_parts(design)
    expected_parts = tuple(parts)

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

    return expected_parts


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
