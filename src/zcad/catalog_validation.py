"""Validate an explicit catalog without exporting CAD artifacts."""

import argparse
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

from zcad_core.validation.design_report import validate_design

from zcad.validation_policy import evaluate_policy, load_policy


def read_catalog(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"schema_version", "designs"}:
        raise ValueError("Catalog must contain schema_version and designs only")
    if value["schema_version"] != "1.0":
        raise ValueError("Unsupported catalog schema_version")
    names = value["designs"]
    if not isinstance(names, list) or not names:
        raise ValueError("Catalog designs must be a nonempty list")
    if any(not isinstance(n, str) or not n.strip() for n in names):
        raise ValueError("Catalog design paths must be nonempty strings")
    paths = [(path.parent / name).resolve() for name in names]
    if len(set(paths)) != len(paths):
        raise ValueError("Catalog contains duplicate design paths")
    return list(zip(names, paths, strict=True))


def run_catalog(arguments, *, read_design, generate_parts, load_printer_profile):
    parser = argparse.ArgumentParser(prog="zcad validate-catalog")
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--printer-profile", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(arguments)
    try:
        entries = read_catalog(args.catalog)
        policy = load_policy(args.policy)
        with redirect_stdout(sys.stderr):
            profile = (
                load_printer_profile(args.printer_profile)
                if args.printer_profile
                else None
            )
    except (OSError, ValueError, TypeError, KeyError) as error:
        result = {
            "schema_version": "1.0",
            "status": "ERROR",
            "error": {"type": type(error).__name__, "message": str(error)},
        }
        print(json.dumps(result) if args.as_json else f"Catalog error: {error}")
        raise SystemExit(2) from None

    results = []
    for name, path in entries:
        try:
            with redirect_stdout(sys.stderr):
                design = read_design(path)
                parts = generate_parts(design)
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
            results.append(
                {
                    "path": name,
                    "status": report["policy_result"]["status"],
                    "report": report,
                }
            )
        except Exception as error:
            # A broken generator must not prevent inspection of later entries.
            # KeyboardInterrupt and SystemExit still terminate the command.
            results.append(
                {
                    "path": name,
                    "status": "ERROR",
                    "error": {"type": type(error).__name__, "message": str(error)},
                }
            )
    counts = {
        status: sum(r["status"] == status for r in results)
        for status in ("PASS", "FAIL", "ERROR")
    }
    status = "ERROR" if counts["ERROR"] else "FAIL" if counts["FAIL"] else "PASS"
    result = {
        "schema_version": "1.0",
        "status": status,
        "policy": policy,
        "design_count": len(results),
        "counts": counts,
        "results": results,
    }
    if args.as_json:
        print(json.dumps(result, indent=2, allow_nan=False))
    else:
        for entry in results:
            print(f"{entry['status']}: {entry['path']}")
            if "error" in entry:
                print(f"  {entry['error']['message']}")
            else:
                for reason in entry["report"]["policy_result"]["reasons"]:
                    print(f"  {reason}")
        print(
            f"Catalog: {status}; {counts['PASS']} passed, "
            f"{counts['FAIL']} failed, {counts['ERROR']} errors"
        )
    if status != "PASS":
        raise SystemExit(2 if status == "ERROR" else 1)
