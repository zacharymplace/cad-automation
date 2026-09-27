"""Read-only validation command for generator design JSON files."""

import argparse
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

from zcad.feature_validation import validate_design
from zcad.validation_policy import evaluate_policy, load_policy


def run_validation(arguments, *, read_design, generate_parts, load_printer_profile):
    """Exit 0 for passed evaluated checks, 1 for failures, 2 for input errors."""
    parser = argparse.ArgumentParser(prog="zcad validate")
    parser.add_argument("design", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--policy", type=Path, help="Versioned validation policy JSON")
    parser.add_argument(
        "--require-check",
        action="append",
        default=[],
        metavar="CODE",
        help="Require every occurrence to PASS; repeatable",
    )
    parser.add_argument("--fail-on-warnings", action="store_true")
    parser.add_argument(
        "--printer-profile",
        type=Path,
        help="Optional profile; omitted profile checks are NOT_CHECKED",
    )
    args = parser.parse_args(arguments)
    try:
        policy = load_policy(
            args.policy,
            required_checks=args.require_check,
            fail_on_warnings=args.fail_on_warnings,
        )
        # Keep machine output clean even if a generator emits diagnostics.
        with redirect_stdout(sys.stderr):
            design = read_design(args.design)
            parts = generate_parts(design)
            profile = (
                load_printer_profile(args.printer_profile)
                if args.printer_profile
                else None
            )
            report = validate_design(
                design_name=design["name"],
                design_type=design["type"],
                parts=parts,
                parameters=design["parameters"],
                printer_profile=profile,
                build_volume_orientation=policy.get(
                    "build_volume_orientation", "generated"
                ),
            )
        report["policy_result"] = evaluate_policy(report, policy)
    except (OSError, ValueError, TypeError, KeyError) as error:
        if args.as_json:
            print(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "status": "ERROR",
                        "error": {"type": type(error).__name__, "message": str(error)},
                    },
                    allow_nan=False,
                )
            )
        else:
            print(f"zcad validate: {error}", file=sys.stderr)
        raise SystemExit(2) from None
    if args.as_json:
        print(json.dumps(report, indent=2, allow_nan=False))
    else:
        print(
            f"Evaluated checks: {report['evaluated_status']} · "
            f"Coverage: {report['coverage']}"
        )
        print(f"Warnings: {report['warning_count']}")
        print(f"Policy: {report['policy_result']['status']}")
        for reason in report["policy_result"]["reasons"]:
            print(f"  {reason}")
        for check in report["checks"]:
            subject = f" ({check['part_name']})" if "part_name" in check else ""
            print(f"{check['status']}: {check['code']}{subject}: {check['message']}")
            for issue in check.get("issues", []):
                print(f"  {issue['severity'].upper()}: {issue['message']}")
    if report["policy_result"]["status"] == "FAIL":
        raise SystemExit(1)
