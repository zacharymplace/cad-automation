"""Generated-part completeness and portable bundle integrity regressions."""

import argparse
import ast
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_bundle import fake_design, fake_export

from zcad.bundle import build_bundle
from zcad.bundle_manifest import MANIFEST_NAME, sha256_file, verify_bundle


@pytest.fixture
def options(tmp_path):
    designs = tmp_path / "designs"
    exports = tmp_path / "exports"
    designs.mkdir()
    exports.mkdir()
    fake_design(designs, "planter", "pixel_heart_planter")
    return dict(
        design_dir=designs,
        exports_dir=exports,
        output_dir=tmp_path / "dist",
        bundle_name="gift",
        title="Gift",
        recipient="R",
    )


def complete(path, exports):
    for name in ("planter", "saucer"):
        fake_export(
            exports,
            design_name="planter",
            design_type="pixel_heart_planter",
            part_name=name,
        )
    return ("planter", "saucer")


def test_manifest_covers_inputs_and_outputs_and_survives_move(options, tmp_path):
    bundle = build_bundle(**options, build_design=complete)
    report = verify_bundle(bundle)
    assert report["design_count"] == 1
    assert report["part_count"] == 2
    assert report["file_count"] == 8  # README, design, six export artifacts
    document = json.loads((bundle / MANIFEST_NAME).read_text())
    assert document["files"]["designs/planter.json"]["sha256"] == sha256_file(
        options["design_dir"] / "planter.json"
    )
    metadata = json.loads(
        (bundle / "metadata/planter-saucer.metadata.json").read_text()
    )
    assert metadata["outputs"] == {
        "step": "step/planter-saucer.step",
        "stl": "stl/planter-saucer.stl",
    }
    moved = tmp_path / "moved"
    shutil.move(bundle, moved)
    verified = verify_bundle(moved, expected_manifest_sha256=report["manifest_sha256"])
    assert verified["trusted_manifest_pinned"] is True


@pytest.mark.parametrize("exported", [("planter",), ("planter", "saucer", "extra")])
def test_missing_or_extra_part_refuses_publication(options, exported):
    previous = build_bundle(**options, build_design=complete)
    original = (previous / MANIFEST_NAME).read_bytes()

    def wrong(path, exports):
        for name in exported:
            fake_export(
                exports,
                design_name="planter",
                design_type="pixel_heart_planter",
                part_name=name,
            )
        return ("planter", "saucer")

    with pytest.raises(ValueError, match="Incomplete or unexpected"):
        build_bundle(**options, build_design=wrong)
    assert (previous / MANIFEST_NAME).read_bytes() == original
    verify_bundle(previous)


@pytest.mark.parametrize(
    "expected", [None, (), ("planter", "planter"), (42,), ["planter"]]
)
def test_invalid_builder_receipt_is_rejected(options, expected):
    def wrong(path, exports):
        complete(path, exports)
        return expected

    with pytest.raises(ValueError, match="unique expected"):
        build_bundle(**options, build_design=wrong)


def test_duplicate_export_part_identity_is_rejected(options):
    def wrong(path, exports):
        complete(path, exports)
        for suffix in (".stl", ".step", ".metadata.json"):
            shutil.copy2(
                exports / ("planter-planter" + suffix), exports / ("duplicate" + suffix)
            )
        return ("planter", "saucer")

    with pytest.raises(ValueError, match="Duplicate exported"):
        build_bundle(**options, build_design=wrong)


@pytest.mark.parametrize("mutation", ["stl", "source", "missing", "extra", "symlink"])
def test_artifact_tampering_is_rejected(options, mutation):
    bundle = build_bundle(**options, build_design=complete)
    if mutation == "stl":
        (bundle / "stl/planter-planter.stl").write_text("changed")
    elif mutation == "source":
        (bundle / "designs/planter.json").write_text("{}")
    elif mutation == "missing":
        (bundle / "step/planter-saucer.step").unlink()
    elif mutation == "extra":
        (bundle / "extra.txt").write_text("extra")
    else:
        (bundle / "link").symlink_to(bundle / "README.md")
    with pytest.raises(ValueError):
        verify_bundle(bundle)


def test_untrusted_manifest_does_not_establish_authenticity(options):
    bundle = build_bundle(**options, build_design=complete)
    pin = verify_bundle(bundle)["manifest_sha256"]
    path = bundle / "stl/planter-planter.stl"
    path.write_text("changed")
    manifest = bundle / MANIFEST_NAME
    document = json.loads(manifest.read_text())
    document["files"]["stl/planter-planter.stl"] = {
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }
    manifest.write_text(json.dumps(document))
    assert verify_bundle(bundle)["trusted_manifest_pinned"] is False
    with pytest.raises(ValueError, match="trusted value"):
        verify_bundle(bundle, expected_manifest_sha256=pin)


@pytest.mark.parametrize(
    "mutation", ["schema", "expected", "path", "duplicate", "identity"]
)
def test_manifest_contract_tampering_is_rejected(options, mutation):
    bundle = build_bundle(**options, build_design=complete)
    path = bundle / MANIFEST_NAME
    document = json.loads(path.read_text())
    if mutation == "schema":
        document["schema"] = "unknown"
    elif mutation == "expected":
        document["designs"][0]["expected_parts"] = ["planter"]
    elif mutation == "path":
        document["files"]["../outside"] = {}
    elif mutation == "duplicate":
        document["designs"].append(document["designs"][0])
    else:
        document["designs"][0]["name"] = "other"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        verify_bundle(bundle)


def test_skip_build_does_not_claim_complete_generated_parts(options):
    complete(None, options["exports_dir"])
    bundle = build_bundle(**options, build=False)
    document = json.loads((bundle / MANIFEST_NAME).read_text())
    assert document["designs"][0]["expected_parts"] is None
    assert verify_bundle(bundle)["mode"] == "reused"


def test_metadata_relocation_preserves_engineering_fields(options):
    def builder(path, exports):
        expected = complete(path, exports)
        for metadata_path in exports.glob("*.metadata.json"):
            metadata = json.loads(metadata_path.read_text())
            metadata.update(
                {
                    "schema_version": "1.0",
                    "git_commit": "recorded-not-attested",
                    "manufacturing": {"material_profile": {"profile_id": "petg"}},
                    "outputs": {
                        "step": "/deleted/stage/part.step",
                        "stl": "/deleted/stage/part.stl",
                    },
                }
            )
            metadata_path.write_text(json.dumps(metadata))
        return expected

    bundle = build_bundle(**options, build_design=builder)
    metadata = json.loads(
        (bundle / "metadata/planter-planter.metadata.json").read_text()
    )
    assert metadata["git_commit"] == "recorded-not-attested"
    assert metadata["manufacturing"]["material_profile"]["profile_id"] == "petg"
    assert metadata["schema_version"] == "1.0"
    assert "/deleted/stage" not in json.dumps(metadata)
    verify_bundle(bundle)


def cli_run_function(**overrides):
    # Execute the real run() body without importing unavailable CAD modules.
    source = Path(__file__).parents[1] / "src/zcad/cli.py"
    function = next(
        n
        for n in ast.parse(source.read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == "run"
    )
    namespace = dict(
        Path=Path, argparse=argparse, json=json, sys=sys, verify_bundle=verify_bundle
    )
    namespace.update(overrides)
    exec(
        compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"),
        namespace,
    )
    return namespace["run"]


def test_cli_captures_part_contract_before_exporter_can_mutate_it():
    parts = {"planter": object(), "saucer": object()}
    args = SimpleNamespace(
        design=Path("design.json"),
        printer_profile=None,
        material_profile=None,
        output=Path("exports"),
    )

    def exporter(request):
        request.parts.clear()
        return SimpleNamespace(design_name="planter", parts=[])

    run = cli_run_function(
        build_parser=lambda: SimpleNamespace(parse_args=lambda argv: args),
        read_design=lambda path: {"name": "planter", "type": "t", "parameters": {}},
        generate_parts=lambda design: parts,
        load_printer_profile=lambda path: None,
        load_material_profile=lambda path: None,
        validate_design_and_parts=lambda **kwargs: [],
        raise_for_validation_errors=lambda issues: None,
        ExportRequest=SimpleNamespace,
        feature_checks=lambda **kwargs: [],
        export_parts=exporter,
    )
    assert run(["design.json"]) == ("planter", "saucer")


def test_cli_verification_dispatch(options, capsys):
    bundle = build_bundle(**options, build_design=complete)
    assert cli_run_function()(["bundle-verify", str(bundle)]) is None
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PASS"
    assert result["part_count"] == 2
