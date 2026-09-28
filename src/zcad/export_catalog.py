"""Run the real exporter against representative designs."""

import argparse
import hashlib
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

from zcad_core.exporters import ExportRequest


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _entries(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        value.get("schema_version") != "1.0"
        or not isinstance(value.get("designs"), list)
        or not value["designs"]
    ):
        raise ValueError("Export catalog requires schema 1.0 and nonempty designs")
    names = value["designs"]
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValueError("Export catalog paths must be nonempty strings")
    paths = [(path.parent / name).resolve() for name in names]
    if len(set(paths)) != len(paths):
        raise ValueError("Export catalog contains duplicate paths")
    return zip(names, paths, strict=True)


def run_export_catalog(
    arguments,
    *,
    read_design,
    generate_parts,
    load_printer_profile,
    export_parts,
    feature_validator,
    stl_feature_validator,
    repository_root,
):
    parser = argparse.ArgumentParser(prog="zcad validate-export-catalog")
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--printer-profile", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(arguments)
    try:
        entries = list(_entries(args.catalog))
        with redirect_stdout(sys.stderr):
            profile = (
                load_printer_profile(args.printer_profile)
                if args.printer_profile
                else None
            )
        output = (
            args.output or Path(tempfile.mkdtemp(prefix="zcad-export-catalog-"))
        ).resolve()
        output.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(
            json.dumps(
                {"schema_version": "1.0", "status": "ERROR", "error": str(error)}
            )
        )
        raise SystemExit(2) from None
    results = []
    for name, path in entries:
        folder = output / Path(name).stem
        try:
            with redirect_stdout(sys.stderr):
                design = read_design(path)
                result = export_parts(
                    ExportRequest(
                        design_name=design["name"],
                        design_type=design["type"],
                        parameters=design.get("parameters", {}),
                        parts=generate_parts(design),
                        output_directory=folder,
                        printer_profile=profile,
                        repository_root=repository_root,
                        feature_validator=feature_validator,
                        stl_feature_validator=stl_feature_validator,
                    )
                )
            files = {}
            for part in result.parts:
                for artifact in (part.step_path, part.stl_path, part.metadata_path):
                    files[str(artifact.relative_to(folder))] = {
                        "sha256": _hash(artifact),
                        "size_bytes": artifact.stat().st_size,
                    }
            results.append({"path": name, "status": "PASS", "files": files})
        except Exception as error:
            results.append(
                {
                    "path": name,
                    "status": "FAIL",
                    "error": {"type": type(error).__name__, "message": str(error)},
                }
            )
    counts = {
        status: sum(item["status"] == status for item in results)
        for status in ("PASS", "FAIL", "ERROR")
    }
    status = "PASS" if counts["FAIL"] == 0 else "FAIL"
    report = {
        "schema_version": "1.0",
        "status": status,
        "scope": "complete export pipeline including STEP/STL round-trip checks",
        "output": str(output),
        "design_count": len(results),
        "counts": counts,
        "results": results,
    }
    print(json.dumps(report, indent=2) if args.as_json else f"Export catalog: {status}")
    if status != "PASS":
        raise SystemExit(1)
