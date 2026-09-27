"""Core gates use the discovered checkout and contribute to run evidence."""

import json
import sys
from pathlib import Path

import pytest

from zcad import local_ci
from zcad.run_integrity import verify


@pytest.mark.parametrize("core_code", [0, 1, 5])
def test_core_gate_cwd_failure_and_integrity(tmp_path, monkeypatch, core_code):
    app, core = tmp_path / "app", tmp_path / "actual-core"
    app.mkdir()
    core.mkdir()
    monkeypatch.setattr(
        local_ci, "repositories", lambda: {"cad-automation": app, "zcad-core": core}
    )
    monkeypatch.setattr(local_ci, "snapshot", lambda p: {"commit": "a", "dirty": False})
    original_gates = local_ci.gates

    def commands(python):
        result = []
        for name, command in original_gates(python):
            if name == "core-tests":
                assert command == [sys.executable, "-m", "pytest", "tests", "-q"]
            script = "from pathlib import Path; print(Path.cwd())"
            if name == "catalog":
                script = 'print(\'{"status":"PASS","design_count":1}\')'
            if name == "core-tests":
                script += f"; raise SystemExit({core_code})"
            result.append((name, [python, "-c", script]))
        return result

    monkeypatch.setattr(local_ci, "gates", commands)
    monkeypatch.setattr(
        sys, "argv", ["local-ci", "--output-parent", str(tmp_path / "reports")]
    )
    with pytest.raises(SystemExit) as caught:
        local_ci.main()
    assert caught.value.code == (1 if core_code else 0)
    folder = next((tmp_path / "reports").iterdir())
    receipt = json.loads((folder / "receipt.json").read_text())
    assert receipt["status"] == ("FAIL" if core_code else "PASS")
    assert [g["name"] for g in receipt["gates"]] == [
        "format",
        "lint",
        "core-tests",
        "tests",
        "viewer",
        "catalog",
    ]
    for gate in receipt["gates"]:
        expected = core if gate["name"] == "core-tests" else app
        assert Path(gate["working_directory"]) == expected
        if gate["name"] != "catalog":
            assert (folder / gate["stdout"]).read_text().strip() == str(expected)
    assert receipt["gates"][2]["returncode"] == core_code
    assert receipt["gates"][-1]["status"] == "PASS"
    assert verify(folder)["file_count"] == 12
    assert verify(folder)["status"] == "PASS"
    (folder / "core-tests.stdout.log").write_text("changed")
    assert verify(folder)["status"] == "FAIL"
