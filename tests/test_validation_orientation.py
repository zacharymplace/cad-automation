import copy
import json

import cadquery as cq
import pytest
from zcad_core.validation.design_report import validate_design

from zcad.catalog_validation import run_catalog
from zcad.validation_cli import run_validation
from zcad.validation_policy import evaluate_policy, load_policy


def policy_file(tmp_path, orientation="xy_90"):
    path = tmp_path / "policy.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "required_checks": ["build_volume"],
                "fail_on_warnings": True,
                "build_volume_orientation": orientation,
            }
        )
    )
    return path


def assess(dimensions, mode="generated", parameters=None):
    return validate_design(
        design_name="fixture",
        design_type="test",
        parts={"main": cq.Workplane().box(*dimensions)},
        printer_profile={
            "build_volume_mm": {"x": 250, "y": 210, "z": 210},
            "minimums_mm": {"wall": 1.2},
        },
        parameters=parameters,
        build_volume_orientation=mode,
    )


@pytest.mark.parametrize(
    "dimensions",
    [
        (170, 215.3, 11.24),
        (150, 210.3, 48),
        (150, 210.3, 73),
        (180, 245.4, 103),
    ],
)
def test_rotation_requires_opt_in_and_preserves_generated_result(dimensions):
    assert assess(dimensions)["evaluated_status"] == "FAIL"
    report = assess(dimensions, "xy_90")
    check = next(c for c in report["checks"] if c["code"] == "build_volume")
    assert report["evaluated_status"] == "PASS"
    assert check["generated_status"] == "FAIL"
    assert check["xy_90_status"] == "PASS"
    assert check["selected_rotation_z_degrees"] == 90
    assert check["actual_mm"] == pytest.approx(dimensions)


@pytest.mark.parametrize(
    "dimensions,expected,rotation",
    [
        ((250, 210, 210), "PASS", 0),
        ((210, 250, 210), "PASS", 90),
        ((210, 250.01, 210), "FAIL", None),
        ((170, 215, 211), "FAIL", None),
        ((251, 251, 10), "FAIL", None),
    ],
)
def test_bounds_and_z_are_not_relaxed(dimensions, expected, rotation):
    report = assess(dimensions, "xy_90")
    check = next(c for c in report["checks"] if c["code"] == "build_volume")
    assert check["status"] == expected
    assert check["selected_rotation_z_degrees"] == rotation


def test_policy_mismatch_warning_and_nonmutation(tmp_path):
    policy = load_policy(policy_file(tmp_path))
    report = assess((170, 215, 10), "xy_90", {"wall": 1.3})
    before = copy.deepcopy(report)
    assert evaluate_policy(report, policy)["status"] == "FAIL"
    assert report == before
    report = assess((170, 215, 10), "xy_90")
    assert evaluate_policy(report, load_policy())["status"] == "FAIL"
    assert evaluate_policy(report, policy)["status"] == "PASS"


@pytest.mark.parametrize("mode", [None, True, "xyz", [], {}])
def test_bad_modes_rejected(tmp_path, mode):
    with pytest.raises(ValueError):
        load_policy(policy_file(tmp_path, mode))


@pytest.mark.parametrize("catalog", [False, True])
def test_commands_forward_policy_without_export(tmp_path, monkeypatch, capsys, catalog):
    policy = policy_file(tmp_path)
    source = tmp_path / "catalog.json"
    source.write_text(json.dumps({"schema_version": "1.0", "designs": ["a.json"]}))
    before = set(tmp_path.iterdir())
    monkeypatch.chdir(tmp_path)
    command = run_catalog if catalog else run_validation
    command(
        [str(source), "--policy", str(policy), "--printer-profile", "p.json", "--json"],
        read_design=lambda p: {"name": "fixture", "type": "test", "parameters": {}},
        generate_parts=lambda d: {"main": cq.Workplane().box(170, 215, 10)},
        load_printer_profile=lambda p: {
            "build_volume_mm": {"x": 250, "y": 210, "z": 210}
        },
    )
    result = json.loads(capsys.readouterr().out)
    report = result["results"][0]["report"] if catalog else result
    assert report["policy_result"]["status"] == "PASS"
    assert set(tmp_path.iterdir()) == before
