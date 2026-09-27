import json
import sys

import pytest

from zcad.local_ci import run_gates, write_receipt
from zcad.run_integrity import bind_artifacts, main, verify


def completed(folder, text="first"):
    receipt = {"status": "FAIL", "started_at": "preserved"}
    run_gates(
        folder,
        folder,
        [("test", [sys.executable, "-c", f"print({text!r})"])],
        receipt,
        10,
    )
    receipt["artifact_integrity"] = bind_artifacts(folder, receipt)
    write_receipt(folder, receipt)
    return receipt


def test_roundtrip_failed_run_and_read_only(tmp_path):
    completed(tmp_path)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    result = verify(tmp_path)
    assert result["status"] == "PASS"
    assert result["run_status"] == "FAIL"
    assert result["file_count"] == 2
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}


@pytest.mark.parametrize("change", ["same_size", "missing", "symlink", "mixed_run"])
def test_changed_artifacts(tmp_path, change):
    completed(tmp_path)
    artifact = tmp_path / "test.stdout.log"
    if change == "same_size":
        artifact.write_text("other\n")
    elif change == "missing":
        artifact.unlink()
    elif change == "symlink":
        artifact.rename(tmp_path / "elsewhere")
        artifact.symlink_to(tmp_path / "elsewhere")
    else:
        other = tmp_path / "other"
        other.mkdir()
        completed(other, "different run")
        artifact.write_bytes((other / artifact.name).read_bytes())
    assert verify(tmp_path)["status"] == "FAIL"


@pytest.mark.parametrize("change", ["traversal", "inventory", "malformed", "running"])
def test_invalid_binding(tmp_path, change):
    receipt = completed(tmp_path)
    if change == "traversal":
        receipt["gates"][0]["stdout"] = "../outside"
    elif change == "inventory":
        del receipt["artifact_integrity"]["files"]["test.stderr.log"]
    elif change == "malformed":
        receipt["artifact_integrity"]["files"]["test.stderr.log"]["size_bytes"] = False
    else:
        receipt["status"] = "RUNNING"
    write_receipt(tmp_path, receipt)
    with pytest.raises(ValueError):
        verify(tmp_path)


def test_legacy_unbound(tmp_path):
    write_receipt(tmp_path, {"status": "PASS"})
    assert verify(tmp_path)["status"] == "UNBOUND"


@pytest.mark.parametrize("changed,code", [(False, 0), (True, 1)])
def test_cli_exit(tmp_path, monkeypatch, capsys, changed, code):
    completed(tmp_path)
    if changed:
        (tmp_path / "test.stderr.log").write_text("modified")
    capsys.readouterr()
    monkeypatch.setattr(sys, "argv", ["verify", str(tmp_path)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == code
    assert json.loads(capsys.readouterr().out)["status"] == (
        "FAIL" if changed else "PASS"
    )
