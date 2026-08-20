from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
repo = root.parent.parent

ci = (root / "ci-local.txt").read_text()
geometry = (root / "geometry-tests.txt").read_text()

required_ci = [
    "471 passed",
    "310 passed",
    "Compatibility contract: PASS",
    "Local CI: PASS",
]

for marker in required_ci:
    if marker not in ci:
        raise SystemExit(
            f"missing CI marker: {marker}"
        )

if "44 passed" not in geometry:
    raise SystemExit(
        "focused geometry suite did not pass"
    )

artifacts = [
    "pico2-enclosure-fit-body.step",
    "pico2-enclosure-fit-body.stl",
    "pico2-enclosure-fit-lid.step",
    "pico2-enclosure-fit-lid.stl",
]

hashes = {}

for name in artifacts:
    path = (
        repo
        / "evidence"
        / "bounded-engineering-package-001"
        / name
    )

    if not path.is_file():
        raise SystemExit(
            f"missing artifact: {name}"
        )

    hashes[name] = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()

receipt = {
    "schema":
        "zcad-engineering-verification-v1",
    "verification_id":
        "engineering-verification-001",
    "result":
        "VERIFIED",
    "claim":
        "bounded-cad-engineering-evidence-ready",
    "validation": {
        "zcad_core_tests": 471,
        "cad_automation_tests": 310,
        "focused_geometry_tests": 44,
        "package_compatibility": "PASS",
    },
    "artifacts_sha256": hashes,
    "boundary": {
        "digital_engineering_evidence":
            True,
        "manufacturing_exports_present":
            True,
        "physical_fit_verified":
            False,
        "production_readiness_proven":
            False,
    },
}

(root / "verification-receipt.json").write_text(
    json.dumps(receipt, indent=2) + "\n"
)

print(
    json.dumps(receipt, indent=2)
)
