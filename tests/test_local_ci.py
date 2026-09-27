import json
import subprocess
import sys

import pytest

from zcad.local_ci import run_gates, snapshot


def test_failure_continues_and_preserves_logs(tmp_path):
    receipt = {"status": "RUNNING"}
    commands = [
        ("bad", [sys.executable, "-c", "print('evidence'); raise SystemExit(1)"]),
        ("good", [sys.executable, "-c", "print('later')"]),
    ]
    run_gates(tmp_path, tmp_path, commands, receipt, 10)
    assert [g["status"] for g in receipt["gates"]] == ["FAIL", "PASS"]
    assert (tmp_path / "bad.stdout.log").read_text().strip() == "evidence"
    assert (tmp_path / "good.stdout.log").read_text().strip() == "later"
    assert (
        json.loads((tmp_path / "receipt.json").read_text())["gates"] == receipt["gates"]
    )


def test_launch_error_continues(tmp_path):
    receipt = {}
    run_gates(
        tmp_path,
        tmp_path,
        [
            ("missing", [str(tmp_path / "absent")]),
            ("good", [sys.executable, "-c", "pass"]),
        ],
        receipt,
        10,
    )
    assert [g["status"] for g in receipt["gates"]] == ["ERROR", "PASS"]


def test_timeout_and_interrupt_checkpoint(tmp_path, monkeypatch):
    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 1)

    monkeypatch.setattr(subprocess, "run", timeout)
    receipt = {}
    run_gates(tmp_path, tmp_path, [("timeout", ["command"])], receipt, 1)
    assert receipt["gates"][0]["status"] == "ERROR"

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(subprocess, "run", interrupt)
    with pytest.raises(KeyboardInterrupt):
        run_gates(tmp_path, tmp_path, [("interrupt", ["command"])], receipt, 1)
    assert (
        json.loads((tmp_path / "receipt.json").read_text())["gates"][0]["status"]
        == "INTERRUPTED"
    )


@pytest.mark.parametrize(
    "payload,status",
    [
        ("not json", "ERROR"),
        ('{"status":"PASS","design_count":0}', "ERROR"),
        ('{"status":"PASS","design_count":3}', "PASS"),
    ],
)
def test_catalog_output_checked(tmp_path, payload, status):
    receipt = {}
    run_gates(
        tmp_path,
        tmp_path,
        [("catalog", [sys.executable, "-c", f"print({payload!r})"])],
        receipt,
        10,
    )
    assert receipt["gates"][0]["status"] == status


def test_real_git_state(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "init",
        ],
        check=True,
    )
    clean = snapshot(tmp_path)
    assert len(clean["commit"]) == 40
    assert clean["dirty"] is False
    (tmp_path / "new.txt").write_text("new")
    assert snapshot(tmp_path)["dirty"] is True


def test_main_receipt_and_changed_state(tmp_path, monkeypatch):
    import zcad.local_ci as runner

    app = tmp_path / "app"
    core = tmp_path / "core"
    app.mkdir()
    core.mkdir()
    monkeypatch.setattr(
        runner,
        "repositories",
        lambda: {"cad-automation": app, "zcad-core": core},
    )
    calls = []

    def state(path):
        calls.append(path)
        return {"commit": "a" if len(calls) <= 2 else "b", "dirty": False}

    monkeypatch.setattr(runner, "snapshot", state)
    monkeypatch.setattr(runner, "gates", lambda p: [("good", [p, "-c", "pass"])])
    monkeypatch.setattr(
        sys, "argv", ["local-ci", "--output-parent", str(tmp_path / "reports")]
    )
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2
    receipt = json.loads(
        next((tmp_path / "reports").glob("*/receipt.json")).read_text()
    )
    assert receipt["observed_git_state_changed"] is True
    assert receipt["status"] == "ERROR"
    from zcad.run_integrity import verify

    folder = next((tmp_path / "reports").iterdir())
    assert verify(folder)["status"] == "PASS"
