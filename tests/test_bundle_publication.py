"""Failure and freshness tests for bundle publication; no CAD dependency."""

import json
import zipfile
from pathlib import Path

import pytest
from test_bundle import fake_design, fake_export

import zcad.bundle as module


@pytest.fixture
def case(tmp_path):
    designs = tmp_path / "designs"
    exports = tmp_path / "exports"
    designs.mkdir()
    exports.mkdir()
    fake_design(designs, "item", "pixel_coaster")
    fake_export(
        exports, design_name="item", design_type="pixel_coaster", part_name="obsolete"
    )
    return dict(
        design_dir=designs,
        exports_dir=exports,
        output_dir=tmp_path / "dist",
        bundle_name="gift",
        title="Gift",
        recipient="R",
    )


def fresh(path, exports):
    design = json.loads(path.read_text())
    fake_export(
        exports,
        design_name=design["name"],
        design_type=design["type"],
        part_name="main",
    )
    return ("main",)


def snapshot(root):
    return {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }


def prior(case):
    root = case["output_dir"]
    (root / "gift").mkdir(parents=True)
    (root / "gift" / "old.txt").write_text("old bundle")
    (root / "gift.zip").write_bytes(b"old zip")
    return snapshot(root / "gift"), (root / "gift.zip").read_bytes()


def assert_prior(case, before):
    root = case["output_dir"]
    assert snapshot(root / "gift") == before[0]
    assert (root / "gift.zip").read_bytes() == before[1]
    assert not (root / ".gift.lock").exists()


def test_fresh_build_excludes_old_parts_and_preserves_exports(case):
    old = snapshot(case["exports_dir"])
    prior(case)
    root = module.build_bundle(**case, build_design=fresh)
    assert sorted(p.name for p in (root / "stl").iterdir()) == ["item.stl"]
    assert (root / "metadata" / "item.metadata.json").is_file()
    assert not (root / "old.txt").exists()
    assert snapshot(case["exports_dir"]) == old
    with zipfile.ZipFile(root.with_suffix(".zip")) as archive:
        for name, data in snapshot(root).items():
            assert archive.read(f"gift/{name}") == data
    assert sorted(p.name for p in root.parent.iterdir()) == ["gift", "gift.zip"]


def test_default_builder_uses_fresh_destination(case, monkeypatch):
    monkeypatch.setattr(module, "_cli_builder", lambda profile: fresh)
    root = module.build_bundle(**case)
    assert (root / "stl" / "item.stl").exists()
    assert not (root / "stl" / "item-obsolete.stl").exists()


@pytest.mark.parametrize(
    "failure", ["builder", "no_output", "guide", "archive", "corrupt"]
)
def test_prepublication_failures_preserve_previous_pair(case, monkeypatch, failure):
    before = prior(case)

    def fail(*args, **kwargs):
        raise RuntimeError("injected")

    builder = fresh
    if failure == "builder":
        builder = fail
    elif failure == "no_output":

        def builder(path, exports):
            return ("main",)
    elif failure == "guide":
        monkeypatch.setattr(module, "write_guide", fail)
    elif failure == "archive":
        monkeypatch.setattr(module.shutil, "make_archive", fail)
    else:

        def corrupt(base, *args):
            path = Path(base + ".zip")
            path.write_bytes(b"not a zip")
            return str(path)

        monkeypatch.setattr(module.shutil, "make_archive", corrupt)
    with pytest.raises((RuntimeError, FileNotFoundError, zipfile.BadZipFile)):
        module.build_bundle(**case, build_design=builder)
    assert_prior(case, before)


@pytest.mark.parametrize("rename_number", [1, 2, 3, 4])
def test_publish_rename_failure_rolls_back_pair(case, monkeypatch, rename_number):
    before = prior(case)
    original = Path.rename
    count = 0

    def rename(self, target):
        nonlocal count
        count += 1
        if count == rename_number:
            raise OSError("injected rename failure")
        return original(self, target)

    monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(OSError, match="injected"):
        module.build_bundle(**case, build_design=fresh)
    assert_prior(case, before)


def test_skip_build_explicitly_discloses_reused_exports(case):
    root = module.build_bundle(**case, build=False)
    assert (root / "stl" / "item-obsolete.stl").exists()
    assert "freshness is unverified" in (root / "README.md").read_text()


@pytest.mark.parametrize("name", ["../gift", "", ".", "/tmp/gift", "a/b", "a\\b"])
def test_unsafe_bundle_names_rejected(case, name):
    case["bundle_name"] = name
    with pytest.raises(ValueError, match="safe filename"):
        module.build_bundle(**case, build_design=fresh)


def test_concurrent_writer_refused(case):
    lock = case["output_dir"] / ".gift.lock"
    lock.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        module.build_bundle(**case, build_design=fresh)
    assert lock.is_dir()


def test_duplicate_design_names_rejected(case):
    (case["design_dir"] / "duplicate.json").write_text(
        (case["design_dir"] / "item.json").read_text()
    )
    with pytest.raises(ValueError, match="Duplicate"):
        module.build_bundle(**case, build_design=fresh)


def test_metadata_type_mismatch_rejected(case):
    def wrong(path, exports):
        fake_export(exports, design_name="item", design_type="tray", part_name="main")
        return ("main",)

    before = prior(case)
    with pytest.raises(ValueError, match="type mismatch"):
        module.build_bundle(**case, build_design=wrong)
    assert_prior(case, before)


def test_output_cannot_replace_input_directory(case):
    case["output_dir"] = case["design_dir"].parent
    case["bundle_name"] = "designs"
    with pytest.raises(ValueError, match="overlaps"):
        module.build_bundle(**case, build_design=fresh)


def test_cli_adapter_passes_staging_and_profile(monkeypatch, tmp_path):
    import sys
    from types import SimpleNamespace

    calls = []

    def run(arguments):
        calls.append(arguments)
        return ("main",)

    monkeypatch.setitem(sys.modules, "zcad.cli", SimpleNamespace(run=run))
    profile = tmp_path / "printer.json"
    design = tmp_path / "design.json"
    exports = tmp_path / "fresh"
    assert module._cli_builder(profile)(design, exports) == ("main",)
    assert calls == [
        [str(design), "--output", str(exports), "--printer-profile", str(profile)]
    ]


def test_failed_rollback_retains_backups(case, monkeypatch):
    before = prior(case)
    original = Path.rename
    count = 0

    def rename(self, target):
        nonlocal count
        count += 1
        if count in (4, 5):
            raise OSError("injected publication and rollback failure")
        return original(self, target)

    monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(OSError):
        module.build_bundle(**case, build_design=fresh)
    stages = list(case["output_dir"].glob(".gift-stage-*"))
    assert len(stages) == 1
    assert snapshot(stages[0] / "previous-gift") == before[0]
    assert (stages[0] / "previous-gift.zip").read_bytes() == before[1]


def test_failed_initial_publication_leaves_no_partial_pair(case, monkeypatch):
    original = Path.rename

    def rename(self, target):
        if self.name == "gift.zip":
            raise OSError("injected")
        return original(self, target)

    monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(OSError):
        module.build_bundle(**case, build_design=fresh)
    assert not (case["output_dir"] / "gift").exists()
    assert not (case["output_dir"] / "gift.zip").exists()
