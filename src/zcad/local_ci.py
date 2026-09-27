"""Local development gates with durable logs and observed Git provenance."""

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def snapshot(root):
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    return {
        "root": str(root),
        "commit": git(root, "rev-parse", "HEAD"),
        "dirty": bool(status),
        "status_porcelain": status,
    }


def repositories():
    app_source = Path(__file__).resolve()
    app = Path(git(app_source.parent, "rev-parse", "--show-toplevel"))
    spec = importlib.util.find_spec("zcad_core")
    if spec is None or spec.origin is None:
        raise ValueError("zcad_core must be installed from a Git checkout")
    core_source = Path(spec.origin).resolve()
    core = Path(git(core_source.parent, "rev-parse", "--show-toplevel"))
    if app == core or app_source != app / "src/zcad/local_ci.py":
        raise ValueError(
            "Expected distinct editable cad-automation and zcad-core checkouts"
        )
    if core_source != core / "src/zcad_core/__init__.py":
        raise ValueError("Imported zcad_core is not the expected source checkout")
    return {"cad-automation": app, "zcad-core": core}


def gates(python):
    return [
        ("format", [python, "-m", "ruff", "format", "--check", "src", "tests"]),
        ("lint", [python, "-m", "ruff", "check", "src", "tests"]),
        ("tests", [python, "-m", "pytest", "tests", "-q"]),
        (
            "catalog",
            [
                python,
                "-m",
                "zcad.cli",
                "validate-catalog",
                "designs/validation-catalog.example.json",
                "--policy",
                "designs/validation-policy.example.json",
                "--printer-profile",
                "profiles/printers/prusa-mk4.json",
                "--json",
            ],
        ),
    ]


def write_receipt(output, receipt):
    temporary = output / "receipt.tmp"
    temporary.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output / "receipt.json")


def run_gates(root, output, commands, receipt, timeout):
    """Continue after failures; checkpoint each gate and retain interrupted logs."""
    receipt["gates"] = []
    for name, command in commands:
        stdout_name = "catalog.json" if name == "catalog" else f"{name}.stdout.log"
        entry = {
            "name": name,
            "command": command,
            "status": "RUNNING",
            "stdout": stdout_name,
            "stderr": f"{name}.stderr.log",
        }
        receipt["gates"].append(entry)
        write_receipt(output, receipt)
        print(f"Running {name}…", flush=True)
        with (
            (output / stdout_name).open("w") as out,
            (output / entry["stderr"]).open("w") as err,
        ):
            try:
                result = subprocess.run(
                    command,
                    cwd=root,
                    stdout=out,
                    stderr=err,
                    timeout=timeout,
                    check=False,
                )
                entry.update(
                    returncode=result.returncode,
                    status="PASS" if result.returncode == 0 else "FAIL",
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                entry.update(status="ERROR", error=str(error))
            except KeyboardInterrupt:
                entry["status"] = "INTERRUPTED"
                write_receipt(output, receipt)
                raise
        if name == "catalog" and entry["status"] == "PASS":
            try:
                report = json.loads((output / stdout_name).read_text())
                if report["status"] != "PASS" or report["design_count"] < 1:
                    raise ValueError("Catalog did not report a nonempty PASS")
            except (ValueError, KeyError, TypeError) as error:
                entry.update(status="ERROR", error=str(error))
        write_receipt(output, receipt)
        print(f"{name}: {entry['status']}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-parent",
        type=Path,
        help="Report parent outside both repositories (default: system temp)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Seconds allowed per gate (default: 1800)",
    )
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        repos = repositories()
        parent = (args.output_parent or Path(tempfile.gettempdir())).resolve()
        if any(parent == root or root in parent.parents for root in repos.values()):
            raise ValueError("Reports must be outside both repositories")
        parent.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="zcad-local-ci-", dir=parent))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"Local CI setup error: {error}\n")
    print(f"Reports: {output}", flush=True)
    receipt = {
        "schema_version": "1.0",
        "status": "RUNNING",
        "started_at": datetime.now(UTC).isoformat(),
        "python": sys.executable,
        "python_version": sys.version,
        "scope": "Automation gates against the imported core checkout; "
        "observed Git state, not an immutable source attestation",
    }
    code = 2
    try:
        receipt["repositories_before"] = {n: snapshot(p) for n, p in repos.items()}
        run_gates(
            repos["cad-automation"],
            output,
            gates(sys.executable),
            receipt,
            args.timeout,
        )
        code = 0 if all(g["status"] == "PASS" for g in receipt["gates"]) else 1
        receipt["status"] = "PASS" if code == 0 else "FAIL"
    except KeyboardInterrupt:
        receipt["status"] = "INTERRUPTED"
        code = 130
    except Exception as error:
        receipt.update(status="ERROR", error=str(error))
    finally:
        try:
            receipt["repositories_after"] = {n: snapshot(p) for n, p in repos.items()}
            receipt["observed_git_state_changed"] = (
                receipt.get("repositories_before") != receipt["repositories_after"]
            )
            if receipt["observed_git_state_changed"] and code == 0:
                receipt["status"] = "ERROR"
                code = 2
        except Exception as error:
            receipt["provenance_error"] = str(error)
            receipt["status"] = "ERROR"
            code = 2
        receipt["finished_at"] = datetime.now(UTC).isoformat()
        receipt["exit_code"] = code
        write_receipt(output, receipt)
    print(f"Local CI: {receipt['status']}; receipt: {output / 'receipt.json'}")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
