import ast
import json
from pathlib import Path

import cadquery as cq
import pytest

from zcad.validation_cli import run_validation


def invoke(args, model=None, reader=None):
    return run_validation(
        args,
        read_design=reader
        or (lambda p: {"name": "fixture", "type": "test", "parameters": {}}),
        generate_parts=lambda d: {
            "main": model if model is not None else cq.Workplane().box(10, 10, 10)
        },
        load_printer_profile=lambda p: {
            "build_volume_mm": {"x": 5, "y": 100, "z": 100}
        },
    )


def test_pass_no_profile_no_files(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    invoke(["fixture.json", "--json"])
    report = json.loads(capsys.readouterr().out)
    assert report["evaluated_status"] == "PASS"
    assert (
        next(c for c in report["checks"] if c["code"] == "build_volume")["status"]
        == "NOT_CHECKED"
    )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "args,model",
    [
        (["fixture.json", "--json", "--printer-profile", "small.json"], None),
        (["fixture.json", "--json"], cq.Workplane().rect(10, 10)),
    ],
)
def test_failed_checks_exit_one(args, model, capsys):
    with pytest.raises(SystemExit) as error:
        invoke(args, model)
    assert error.value.code == 1
    assert json.loads(capsys.readouterr().out)["evaluated_status"] == "FAIL"


def test_input_error_is_json_and_exit_two(capsys):
    def missing(path):
        print("loader diagnostic")
        raise FileNotFoundError("missing design")

    with pytest.raises(SystemExit) as error:
        invoke(["missing.json", "--json"], reader=missing)
    assert error.value.code == 2
    output = capsys.readouterr()
    assert json.loads(output.out)["status"] == "ERROR"
    assert "loader diagnostic" in output.err


def test_human_output(capsys):
    invoke(["fixture.json"])
    assert "Coverage: PARTIAL" in capsys.readouterr().out


def test_real_dispatch(monkeypatch):
    import zcad.validation_cli as command

    calls = []
    monkeypatch.setattr(
        command, "run_validation", lambda args, **kwargs: calls.append(args)
    )
    source = Path(__file__).parents[1] / "src/zcad/cli.py"
    run = next(
        n
        for n in ast.parse(source.read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == "run"
    )
    namespace = dict(read_design=None, generate_parts=None, load_printer_profile=None)
    exec(
        compile(ast.Module(body=[run], type_ignores=[]), str(source), "exec"), namespace
    )
    namespace["run"](["validate", "fixture.json", "--json"])
    assert calls == [["fixture.json", "--json"]]
