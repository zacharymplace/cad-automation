import copy
import json

import pytest
from test_validation_cli import invoke

from zcad.validation_policy import evaluate_policy, load_policy


def test_required_unchecked_and_unknown_exit_one(capsys):
    for code in ("build_volume", "typo"):
        with pytest.raises(SystemExit) as error:
            invoke(["fixture.json", "--json", "--require-check", code])
        assert error.value.code == 1
        report = json.loads(capsys.readouterr().out)
        assert report["evaluated_status"] == "PASS"
        assert report["coverage"] == "PARTIAL"
        assert report["policy_result"]["status"] == "FAIL"


def test_required_geometry_passes_without_files(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    invoke(["fixture.json", "--json", "--require-check", "solid_topology"])
    assert json.loads(capsys.readouterr().out)["policy_result"]["status"] == "PASS"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("status", ["FAIL", "NOT_CHECKED"])
def test_all_parts_required_and_evidence_unchanged(status):
    report = {
        "evaluated_status": "PASS",
        "warning_count": 0,
        "checks": [
            {"code": "build_volume", "status": "PASS", "part_name": "first"},
            {"code": "build_volume", "status": status, "part_name": "second"},
        ],
    }
    before = copy.deepcopy(report)
    result = evaluate_policy(report, load_policy(required_checks=["build_volume"]))
    assert result["status"] == "FAIL"
    assert "second" in result["reasons"][0]
    assert report == before


def test_warning_gate_and_failed_evidence():
    report = {"evaluated_status": "PASS", "warning_count": 1, "checks": []}
    assert evaluate_policy(report, load_policy())["status"] == "PASS"
    assert (
        evaluate_policy(report, load_policy(fail_on_warnings=True))["status"] == "FAIL"
    )
    report["evaluated_status"] = "FAIL"
    assert evaluate_policy(report, load_policy())["status"] == "FAIL"


def test_file_policy_cli_additions_and_integration(tmp_path, capsys):
    path = tmp_path / "policy.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "required_checks": ["build_volume"],
                "fail_on_warnings": True,
            }
        )
    )
    policy = load_policy(path, required_checks=["shape_stack", "shape_stack"])
    assert policy["required_checks"] == ["build_volume", "shape_stack"]
    assert policy["fail_on_warnings"] is True
    with pytest.raises(SystemExit) as error:
        invoke(["fixture.json", "--json", "--policy", str(path)])
    assert error.value.code == 1
    assert json.loads(capsys.readouterr().out)["policy_result"][
        "policy"
    ] == load_policy(path)


@pytest.mark.parametrize(
    "value",
    [
        [],
        {},
        {"schema_version": "2.0"},
        {"schema_version": "1.0", "required_checks": [], "fail_on_warnings": "false"},
        {"schema_version": "1.0", "required_checks": "wall", "fail_on_warnings": False},
        {
            "schema_version": "1.0",
            "required_checks": [False],
            "fail_on_warnings": False,
        },
        {"schema_version": "1.0", "required_checks": [" "], "fail_on_warnings": False},
        {
            "schema_version": "1.0",
            "required_checks": [],
            "fail_on_warnings": False,
            "typo": True,
        },
    ],
)
def test_bad_policy_input_exit_two(tmp_path, capsys, value):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(value))
    with pytest.raises(SystemExit) as error:
        invoke(["fixture.json", "--json", "--policy", str(path)])
    assert error.value.code == 2
    assert json.loads(capsys.readouterr().out)["status"] == "ERROR"
