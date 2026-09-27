import ast
import json
from pathlib import Path

import cadquery as cq
import pytest

from zcad.catalog_validation import run_catalog


def setup_catalog(tmp_path, names):
    catalog = tmp_path / "catalog.json"
    policy = tmp_path / "policy.json"
    catalog.write_text(json.dumps({"schema_version": "1.0", "designs": names}))
    policy.write_text(
        json.dumps(
            {"schema_version": "1.0", "required_checks": [], "fail_on_warnings": False}
        )
    )
    return [str(catalog), "--policy", str(policy), "--json"]


def invoke(args, seen):
    def read(path):
        seen.append(path)
        if path.stem == "missing":
            raise FileNotFoundError("missing fixture")
        return {"name": path.stem, "type": "test", "parameters": {}}

    def generate(design):
        print("generator diagnostic")
        if design["name"] == "broken":
            raise RuntimeError("kernel failure")
        return {
            "main": cq.Workplane().rect(10, 10)
            if design["name"] == "bad"
            else cq.Workplane().box(10, 10, 10)
        }

    run_catalog(
        args,
        read_design=read,
        generate_parts=generate,
        load_printer_profile=lambda p: None,
    )


@pytest.mark.parametrize(
    "names,exit_code,counts",
    [
        (["good.json"], 0, {"PASS": 1, "FAIL": 0, "ERROR": 0}),
        (["bad.json", "good.json"], 1, {"PASS": 1, "FAIL": 1, "ERROR": 0}),
        (
            ["missing.json", "bad.json", "broken.json", "good.json"],
            2,
            {"PASS": 1, "FAIL": 1, "ERROR": 2},
        ),
    ],
)
def test_aggregate_continue_and_no_exports(
    tmp_path, monkeypatch, capsys, names, exit_code, counts
):
    args = setup_catalog(tmp_path, names)
    monkeypatch.chdir(tmp_path.parent)
    before = set(tmp_path.iterdir())
    seen = []
    if exit_code:
        with pytest.raises(SystemExit) as error:
            invoke(args, seen)
        assert error.value.code == exit_code
    else:
        invoke(args, seen)
    output = capsys.readouterr()
    report = json.loads(output.out)
    assert report["counts"] == counts
    assert report["design_count"] == len(names)
    assert [r["path"] for r in report["results"]] == names
    assert seen == [tmp_path / n for n in names]
    assert set(tmp_path.iterdir()) == before
    assert "generator diagnostic" in output.err


@pytest.mark.parametrize("names", [[], ["a.json", "./a.json"], [False], "a.json"])
def test_invalid_catalog_is_error_before_generation(tmp_path, capsys, names):
    seen = []
    with pytest.raises(SystemExit) as error:
        invoke(setup_catalog(tmp_path, names), seen)
    assert error.value.code == 2
    assert seen == []
    assert json.loads(capsys.readouterr().out)["status"] == "ERROR"


def test_policy_failure_and_human_output(tmp_path, capsys):
    args = setup_catalog(tmp_path, ["good.json"])
    (tmp_path / "policy.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "required_checks": ["build_volume"],
                "fail_on_warnings": False,
            }
        )
    )
    with pytest.raises(SystemExit) as error:
        invoke(args[:-1], [])
    assert error.value.code == 1
    assert "NOT_CHECKED" in capsys.readouterr().out


def test_catalog_dispatch(monkeypatch):
    import zcad.catalog_validation as command

    calls = []
    monkeypatch.setattr(command, "run_catalog", lambda args, **kw: calls.append(args))
    path = Path(__file__).parents[1] / "src/zcad/cli.py"
    run = next(
        n
        for n in ast.parse(path.read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == "run"
    )
    namespace = dict(read_design=None, generate_parts=None, load_printer_profile=None)
    exec(compile(ast.Module(body=[run], type_ignores=[]), str(path), "exec"), namespace)
    namespace["run"](["validate-catalog", "catalog.json"])
    assert calls == [["catalog.json"]]
