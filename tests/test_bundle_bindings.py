"""Original export bindings must agree before a new bundle seals input bytes."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from test_bundle import fake_design, fake_export
from test_bundle_publication import assert_prior, prior, snapshot

from zcad.bundle import build_bundle
from zcad.bundle_manifest import verify_bundle


def add_bindings(metadata: Path) -> None:
    record = json.loads(metadata.read_text())
    stem = metadata.name.removesuffix(".metadata.json")
    record["producer"] = {"git_commit": "core-revision"}
    record["git_commit"] = "consumer-revision"
    record["artifacts"] = {
        kind: {
            "filename": f"{stem}.{kind}",
            "sha256": hashlib.sha256(
                (metadata.parent / f"{stem}.{kind}").read_bytes()
            ).hexdigest(),
            "size_bytes": (metadata.parent / f"{stem}.{kind}").stat().st_size,
        }
        for kind in ("step", "stl")
    }
    metadata.write_text(json.dumps(record))


@pytest.fixture
def case(tmp_path):
    designs, exports = tmp_path / "designs", tmp_path / "exports"
    designs.mkdir()
    exports.mkdir()
    fake_design(designs, "item", "pixel_coaster")
    fake_export(
        exports, design_name="item", design_type="pixel_coaster", part_name="main"
    )
    add_bindings(exports / "item.metadata.json")
    return dict(
        design_dir=designs,
        exports_dir=exports,
        output_dir=tmp_path / "dist",
        bundle_name="gift",
        title="Gift",
        recipient="R",
    )


@pytest.mark.parametrize("multi", [False, True])
@pytest.mark.parametrize("fresh", [False, True])
def test_matching_bindings_preserve_layout_fields_and_inputs(case, multi, fresh):
    if multi:
        fake_export(
            case["exports_dir"],
            design_name="item",
            design_type="pixel_coaster",
            part_name="cap",
        )
        add_bindings(case["exports_dir"] / "item-cap.metadata.json")
    before = snapshot(case["exports_dir"])

    def builder(path, destination):
        for source in case["exports_dir"].iterdir():
            shutil.copy2(source, destination / source.name)
        return ("main", "cap") if multi else ("main",)

    root = build_bundle(**case, build=fresh, build_design=builder)
    assert verify_bundle(root)["status"] == "PASS"
    assert snapshot(case["exports_dir"]) == before
    assert {p.name for p in root.iterdir() if p.is_dir()} == {
        "step",
        "stl",
        "metadata",
        "designs",
    }
    for name in ["item", "item-cap"] if multi else ["item"]:
        original = json.loads(before[f"{name}.metadata.json"])
        bundled = json.loads((root / "metadata" / f"{name}.metadata.json").read_text())
        for field in ("artifacts", "producer", "git_commit"):
            assert bundled[field] == original[field]
        assert bundled["outputs"] == {
            "step": f"step/{name}.step",
            "stl": f"stl/{name}.stl",
        }
        assert bundled["bundle_output_path_base"] == "bundle_root"
    assert (
        "STEP and STL matched recorded export bindings"
        in (root / "README.md").read_text()
    )


@pytest.mark.parametrize("fresh", [False, True])
@pytest.mark.parametrize(
    "failure",
    [
        "hash",
        "size",
        "missing",
        "partial",
        "malformed",
        "redirect",
        "symlink",
        "unsafe",
        "unreadable",
    ],
)
def test_binding_failure_preserves_old_bundle_zip_and_inputs(
    case, failure, fresh, monkeypatch
):
    exports = case["exports_dir"]
    metadata = exports / "item.metadata.json"
    record = json.loads(metadata.read_text())
    step = exports / "item.step"
    if failure == "hash":
        step.write_bytes(b"x" * step.stat().st_size)
    elif failure == "size":
        record["artifacts"]["step"]["size_bytes"] += 1
    elif failure == "missing":
        step.unlink()
    elif failure == "partial":
        del record["artifacts"]["stl"]
    elif failure == "malformed":
        record["artifacts"] = None
    elif failure == "redirect":
        (exports / "other.step").write_bytes(step.read_bytes())
        record["artifacts"]["step"]["filename"] = "other.step"
    elif failure == "unsafe":
        record["artifacts"]["step"]["filename"] = "../outside.step"
    elif failure == "unreadable":
        from zcad_core.exporters import verification

        original = verification._read_bytes_identity

        def deny(path):
            if path.name == "item.step":
                raise PermissionError("fixture: unreadable STEP")
            return original(path)

        monkeypatch.setattr(verification, "_read_bytes_identity", deny)
    else:
        step.unlink()
        step.symlink_to(exports / "item.stl")
    metadata.write_text(json.dumps(record))
    before_inputs, before_outputs = snapshot(exports), prior(case)

    def builder(path, destination):
        for source in exports.iterdir():
            shutil.copy2(source, destination / source.name, follow_symlinks=False)
        return ("main",)

    with pytest.raises((ValueError, FileNotFoundError)):
        build_bundle(**case, build=fresh, build_design=builder)
    assert_prior(case, before_outputs)
    assert snapshot(exports) == before_inputs


def test_legacy_absent_bindings_remain_usable_but_not_claimed_verified(case):
    metadata = case["exports_dir"] / "item.metadata.json"
    record = json.loads(metadata.read_text())
    del record["artifacts"]
    metadata.write_text(json.dumps(record))
    root = build_bundle(**case, build=False)
    assert verify_bundle(root)["status"] == "PASS"
    guide = (root / "README.md").read_text()
    assert "not checked: legacy metadata has no artifact bindings" in guide
    assert "freshness is unverified" in guide


def test_relocated_sibling_exports_work(case):
    moved = case["exports_dir"].with_name("moved")
    case["exports_dir"].rename(moved)
    case["exports_dir"] = moved
    assert verify_bundle(build_bundle(**case, build=False))["status"] == "PASS"


def test_mixed_legacy_and_bound_parts_disclose_each_scope(case):
    exports = case["exports_dir"]
    fake_export(
        exports, design_name="item", design_type="pixel_coaster", part_name="cap"
    )
    root = build_bundle(**case, build=False)
    assert verify_bundle(root)["status"] == "PASS"
    guide = (root / "README.md").read_text()
    assert "- item: STEP and STL matched recorded export bindings." in guide
    assert (
        "- item (cap): not checked: legacy metadata has no artifact bindings." in guide
    )
