"""Real geometry and failure evidence for revision-bound enclosure reports."""

import json
from pathlib import Path

import cadquery as cq
import pytest
from zcad_core.validation.stl_mesh import read_stl

import zcad.enclosure_acceptance as acceptance


@pytest.fixture(scope="module")
def accepted_package(tmp_path_factory):
    folder = tmp_path_factory.mktemp("acceptance-reference")
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-enclosure-fit.json", folder, "reference-test"
    )
    return folder, report


def test_reference_records_checks_sources_and_artifacts(accepted_package):
    folder, report = accepted_package
    assert report["digital_status"] == "DIGITAL_CHECKS_PASSED"
    assert report["physical_status"] == "PENDING"
    assert report["dimensions_mm"]["body"]["z"] == pytest.approx(12)
    assert report["dimensions_mm"]["assembled"]["z"] == pytest.approx(14.8)
    assert len(report["hardware_placements"]) == 8
    assert report["hardware"]["board_component_catalog"]["source_model_sha256"]
    assert report["sources"]["core"]["source_sha256"]
    assert report["sources"]["product"]["source_sha256"]
    assert set(report["artifacts"]) == {
        "body.step",
        "body.stl",
        "lid.step",
        "lid.stl",
        "design.json",
        "acceptance-profile.json",
        "report.md",
    }
    assert report["acceptance_profile"]["identifier"] == "pico2-digital-baseline"
    assert report["acceptance_profile"]["status"] == "PASS"
    assert report["acceptance_profile"]["policy"]["required_checks"]
    envelope = next(
        check
        for check in report["checks"]
        if check["code"] == "maximum_enclosure_envelope"
    )
    assert envelope["status"] == "PASS"
    assert envelope["maximum_mm"] == {"width": 40, "depth": 65, "height": 20}
    checks = report["checks"]
    assert not any(check["status"] == "FAIL" for check in checks)
    assert sum(check["code"] == "mounting_bore_alignment" for check in checks) == 4
    assert (
        sum(check["code"] == "hardware_enclosure_collision" for check in checks) == 16
    )
    assert (
        next(check for check in checks if check["code"] == "usb_plug_insertion_path")[
            "status"
        ]
        == "NOT_CHECKED"
    )
    exports = [
        check for check in checks if check["code"] == "export_artifact_integrity"
    ]
    assert {check["subject"] for check in exports} == {"body", "lid"}
    assert all(check["status"] == "PASS" for check in exports)
    for check in exports:
        assert set(check["exports"]) == {"step", "stl"}
        assert all(
            artifact["size_bytes"] > 0
            and len(artifact["sha256"]) == 64
            and artifact["status"] == "PASS"
            for artifact in check["exports"].values()
        )
        assert all(
            report["artifacts"][artifact["path"]]
            == {
                "sha256": artifact["sha256"],
                "size_bytes": artifact["size_bytes"],
            }
            for artifact in check["exports"].values()
        )
    assert "export_artifact_integrity" in (folder / "report.md").read_text()
    verification = acceptance.verify_acceptance(folder)
    assert verification["package_integrity"] == "PASS"
    assert verification["report_consistency"] == "PASS"
    assert verification["acceptance_outcome"] == "DIGITAL_CHECKS_PASSED"
    assert verification["authenticity"] == "UNVERIFIED"
    pinned = acceptance.verify_acceptance(
        folder, expected_report_sha256=verification["report_sha256"]
    )
    assert pinned["authenticity"] == "MATCHED_TRUSTED_SHA256"
    assert pinned["trusted_report_sha256"] == verification["report_sha256"]


def test_step_round_trip_rejects_same_bounds_and_volume_with_different_geometry(
    tmp_path,
):
    source = cq.Workplane("XY").box(10, 10, 10)
    left_cavity = cq.Workplane("XY").box(2, 2, 2).translate((-2, 0, 0))
    right_cavity = cq.Workplane("XY").box(2, 2, 2).translate((2, 0, 0))
    variant = source.cut(right_cavity)
    source = source.cut(left_cavity)
    output = tmp_path / "artifacts"
    output.mkdir()
    cq.exporters.export(variant, str(output / "part.step"), exportType="STEP")
    cq.exporters.export(source, str(output / "part.stl"), exportType="STL")

    check = acceptance._export_artifact_check("part", source, output)

    step = check["exports"]["step"]
    assert step["dimensions_mm"] == pytest.approx([10, 10, 10])
    assert step["volume_mm3"] == pytest.approx(step["source_volume_mm3"])
    assert step["symmetric_difference_volume_mm3"] == pytest.approx(16)
    assert step["status"] == "FAIL"
    assert check["status"] == "FAIL"


def test_stl_geometry_comparison_detects_same_bounds_and_volume_change(tmp_path):
    source = cq.Workplane("XY").box(10, 10, 10)
    left_cavity = cq.Workplane("XY").box(3, 3, 3).translate((-2, 0, 0))
    right_cavity = cq.Workplane("XY").box(3, 3, 3).translate((2, 0, 0))
    variant = source.cut(right_cavity)
    source = source.cut(left_cavity)
    output = tmp_path / "artifacts"
    output.mkdir()
    cq.exporters.export(source, str(output / "part.step"), exportType="STEP")
    cq.exporters.export(variant, str(output / "part.stl"), exportType="STL")

    check = acceptance._export_artifact_check("part", source, output)

    stl = check["exports"]["stl"]
    comparison = stl["geometry_comparison"]
    assert stl["dimensions_mm"] == pytest.approx([10, 10, 10])
    assert stl["volume_mm3"] == pytest.approx(stl["source_volume_mm3"], abs=0.01)
    assert comparison["sample_count"] == acceptance.STL_GEOMETRY_SAMPLE_COUNT
    assert comparison["mismatching_samples"] > 0
    assert (
        comparison["estimated_symmetric_difference_volume_mm3"]
        > stl["tolerance"]["estimated_symmetric_difference_volume_mm3"]
    )
    assert stl["status"] == "FAIL"
    assert check["status"] == "FAIL"


@pytest.mark.parametrize("size", [0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
@pytest.mark.parametrize("position", [(5, 5, 5), (-3, 4, -2), (4, -3, 3)])
def test_stl_sampling_detection_boundary_for_moved_cubic_cavity(
    tmp_path, size, position
):
    base = cq.Workplane("XY").box(20, 20, 20)
    source = base.cut(cq.Workplane("XY").box(size, size, size).translate((-4, 0, 0)))
    variant = base.cut(cq.Workplane("XY").box(size, size, size).translate(position))
    stl_path = tmp_path / "variant.stl"
    cq.exporters.export(variant, str(stl_path), exportType="STL")
    mesh, _ = read_stl(stl_path.read_bytes())

    comparison = acceptance._sampled_stl_geometry_comparison(source.val(), mesh)
    tolerance = acceptance._stl_geometry_tolerance(source.val().Volume())

    source_bounds = source.val().BoundingBox()
    variant_bounds = variant.val().BoundingBox()
    assert (
        source_bounds.xlen,
        source_bounds.ylen,
        source_bounds.zlen,
    ) == pytest.approx(
        (
            variant_bounds.xlen,
            variant_bounds.ylen,
            variant_bounds.zlen,
        )
    )
    assert source.val().Volume() == pytest.approx(variant.val().Volume())
    assert (comparison["estimated_symmetric_difference_volume_mm3"] > tolerance) is (
        size >= 3.0
    )


@pytest.mark.parametrize(
    "sample_count,position,expected_detected",
    [
        (512, (5, 5, 5), True),
        (512, (-3, 4, -2), False),
        (512, (4, -3, 3), True),
        (1024, (5, 5, 5), True),
        (1024, (-3, 4, -2), True),
        (1024, (4, -3, 3), True),
        (2048, (5, 5, 5), True),
        (2048, (-3, 4, -2), True),
        (2048, (4, -3, 3), True),
    ],
)
def test_stl_sample_count_boundary_for_three_mm_moved_cavity(
    tmp_path, monkeypatch, sample_count, position, expected_detected
):
    monkeypatch.setattr(acceptance, "STL_GEOMETRY_SAMPLE_COUNT", sample_count)
    base = cq.Workplane("XY").box(20, 20, 20)
    source = base.cut(cq.Workplane("XY").box(3, 3, 3).translate((-4, 0, 0)))
    variant = base.cut(cq.Workplane("XY").box(3, 3, 3).translate(position))
    stl_path = tmp_path / "variant.stl"
    cq.exporters.export(variant, str(stl_path), exportType="STL")
    mesh, _ = read_stl(stl_path.read_bytes())

    comparison = acceptance._sampled_stl_geometry_comparison(source.val(), mesh)
    tolerance = acceptance._stl_geometry_tolerance(source.val().Volume())

    assert comparison["sample_count"] == sample_count
    assert (
        comparison["estimated_symmetric_difference_volume_mm3"] > tolerance
    ) is expected_detected


def test_plug_insertion_report_names_method_and_assumptions(tmp_path):
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-oled-clips-usb-test-envelope.json",
        tmp_path,
        "plug-insertion-assumptions",
    )
    insertion = next(
        check
        for check in report["checks"]
        if check["code"] == "usb_plug_insertion_path"
    )
    assert insertion["status"] == "PASS"
    assert "negative Y" in insertion["method"]
    assert "no tilt or rotation" in insertion["assumptions"][1]
    assert "does not establish real-cable" in insertion["scope_limit"]
    markdown = (tmp_path / "report.md").read_text()
    assert "usb_plug_insertion_path" in markdown
    assert "negative Y" in markdown
    assert "does not establish real-cable" in markdown


def test_obstructed_usb_insertion_path_is_rejected(monkeypatch, tmp_path):
    original = acceptance.build_pico2_enclosure_fit

    def obstructed(parameters):
        parts = original(parameters)
        # Add a cross-wall barrier on the plug's insertion axis while retaining
        # a valid solid body for the normal export checks.
        barrier = (
            cq.Workplane("XY")
            .box(20, 2, 8, centered=(True, True, False))
            .translate((0, -parameters.outer_depth_mm / 2 + 0.5, 0))
        )
        parts["body"] = parts["body"].union(barrier)
        return parts

    monkeypatch.setattr(acceptance, "build_pico2_enclosure_fit", obstructed)
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-oled-clips-usb-test-envelope.json",
        tmp_path,
        "blocked-usb-path",
    )
    insertion = next(
        check
        for check in report["checks"]
        if check["code"] == "usb_plug_insertion_path"
    )
    assert insertion["status"] == "FAIL"
    assert insertion["housing_path_intersection_with_body_mm3"] > 0
    assert report["digital_status"] == "REVISION_REQUIRED"
    assert not list(tmp_path.glob("*.step"))


def test_custom_module_and_offsets_are_bound_to_report(tmp_path):
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-custom-oled.synthetic.json", tmp_path, "custom-test"
    )
    assert report["digital_status"] == "REVISION_REQUIRED"
    assert report["hardware"]["display"]["identifier"] == "SYNTHETIC_PICO_CALIBRATION"
    assert report["dimensions_mm"]["body"]["x"] == pytest.approx(43.9)
    assert report["dimensions_mm"]["body"]["z"] == pytest.approx(15)
    envelope = next(
        check
        for check in report["checks"]
        if check["code"] == "maximum_enclosure_envelope"
    )
    assert envelope["status"] == "FAIL"
    assert envelope["exceeded_dimensions"] == ["width"]
    window = next(
        check for check in report["checks"] if check["code"] == "display_window_opening"
    )
    assert window["center_mm"] == [3, 8]
    assert window["status"] == "PASS"


def test_strict_profile_rejects_missing_plug_and_oled_evidence(tmp_path):
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-enclosure-fit.json",
        tmp_path,
        "strict-profile-missing-hardware",
        profile_path=("designs/acceptance-profiles/pico2-plug-oled-model.json"),
    )
    assert report["digital_status"] == "REVISION_REQUIRED"
    assert report["acceptance_profile"]["status"] == "FAIL"
    assert any(
        "Required check usb_plug_insertion_path" in reason
        for reason in report["acceptance_profile"]["reasons"]
    )
    summary = (tmp_path / "report.md").read_text()
    assert "Required check usb_plug_insertion_path" in summary
    assert "Required check oled_retention" in summary
    verification = acceptance.verify_acceptance(tmp_path)
    assert verification["package_integrity"] == "PASS"
    assert verification["report_consistency"] == "PASS"
    assert verification["acceptance_outcome"] == "REVISION_REQUIRED"


def test_modeled_plug_and_oled_profile_passes_synthetic_fixture(tmp_path):
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-oled-clips-usb-test-envelope.json",
        tmp_path,
        "modeled-plug-oled",
        profile_path="designs/acceptance-profiles/pico2-plug-oled-model.json",
    )
    assert report["digital_status"] == "DIGITAL_CHECKS_PASSED"
    assert report["acceptance_profile"]["status"] == "PASS"
    assert report["hardware"]["usb_plug"]["evidence_status"] == "test_envelope"


def test_profiles_apply_distinct_envelopes_to_the_same_synthetic_design(tmp_path):
    design = json.loads(
        Path("designs/calibration/pico2-oled-clips-synthetic.json").read_text()
    )
    plug_design = json.loads(
        Path("designs/calibration/pico2-oled-clips-usb-test-envelope.json").read_text()
    )
    design["parameters"]["usb_plug"] = plug_design["parameters"]["usb_plug"]
    design_path = tmp_path / "synthetic-oled-with-plug-envelope.json"
    design_path.write_text(json.dumps(design))

    baseline = acceptance.build_acceptance(
        design_path, tmp_path / "baseline", "synthetic-default-profile"
    )
    plug_oled = acceptance.build_acceptance(
        design_path,
        tmp_path / "plug-oled",
        "synthetic-plug-oled-profile",
        profile_path="designs/acceptance-profiles/pico2-plug-oled-model.json",
    )
    assert (
        baseline["dimensions_mm"]["assembled"]
        == plug_oled["dimensions_mm"]["assembled"]
    )
    assert baseline["digital_status"] == "REVISION_REQUIRED"
    baseline_envelope = next(
        check
        for check in baseline["checks"]
        if check["code"] == "maximum_enclosure_envelope"
    )
    assert baseline_envelope["exceeded_dimensions"] == ["width", "height"]
    baseline_summary = (tmp_path / "baseline" / "report.md").read_text()
    assert (
        "Maximum assembled envelope (mm): 40.000 × 65.000 × 20.000" in baseline_summary
    )
    assert "exceeds width, height" in baseline_summary
    assert plug_oled["digital_status"] == "DIGITAL_CHECKS_PASSED"
    strict_envelope = next(
        check
        for check in plug_oled["checks"]
        if check["code"] == "maximum_enclosure_envelope"
    )
    assert strict_envelope["maximum_mm"] == {"width": 45, "depth": 60, "height": 25}
    assert strict_envelope["status"] == "PASS"
    strict_summary = (tmp_path / "plug-oled" / "report.md").read_text()
    assert "Maximum assembled envelope (mm): 45.000 × 60.000 × 25.000" in strict_summary
    for folder in (tmp_path / "baseline", tmp_path / "plug-oled"):
        assert acceptance.verify_acceptance(folder)["report_consistency"] == "PASS"


def test_optional_maximum_envelope_rejects_oversized_assembly(tmp_path):
    source = json.loads(
        Path("designs/calibration/pico2-enclosure-fit.json").read_text()
    )
    source["parameters"]["lid_clearance_mm"] = 100.0
    design_path = tmp_path / "oversized-design.json"
    design_path.write_text(json.dumps(source))
    profile_path = tmp_path / "bounded-profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "schema_version": "1.2",
                "required_checks": [],
                "fail_on_warnings": False,
                "maximum_enclosure_envelope_mm": {
                    "width": 100,
                    "depth": 100,
                    "height": 100,
                },
            }
        )
    )
    within_limit = acceptance.build_acceptance(
        "designs/calibration/pico2-enclosure-fit.json",
        tmp_path / "within-envelope",
        "within-envelope",
        profile_path=profile_path,
    )
    within_check = next(
        item
        for item in within_limit["checks"]
        if item["code"] == "maximum_enclosure_envelope"
    )
    assert within_check["status"] == "PASS"
    assert within_limit["digital_status"] == "DIGITAL_CHECKS_PASSED"
    assert (
        acceptance.verify_acceptance(tmp_path / "within-envelope")["report_consistency"]
        == "PASS"
    )

    output = tmp_path / "acceptance"
    report = acceptance.build_acceptance(
        design_path,
        output,
        "oversized-envelope",
    )
    check = next(
        item
        for item in report["checks"]
        if item["code"] == "maximum_enclosure_envelope"
    )
    assert check["status"] == "FAIL"
    assert check["measured_mm"]["width"] > 200
    assert check["exceeded_dimensions"] == ["width", "depth"]
    assert report["digital_status"] == "REVISION_REQUIRED"
    assert report["acceptance_profile"]["status"] == "FAIL"
    summary = (output / "report.md").read_text()
    assert "Maximum assembled envelope (mm): 40.000 × 65.000 × 20.000" in summary
    assert "exceeds width, depth" in summary
    assert not any(
        item["code"] == "export_artifact_integrity" for item in report["checks"]
    )
    verification = acceptance.verify_acceptance(output)
    assert verification["package_integrity"] == "PASS"
    assert verification["report_consistency"] == "PASS"

    report_path = output / "report.json"
    tampered = json.loads(report_path.read_text())
    tampered["dimensions_mm"]["assembled"]["x"] = 50
    report_path.write_text(json.dumps(tampered))
    verification = acceptance.verify_acceptance(output)
    assert verification["report_consistency"] == "FAIL"
    assert any(
        "maximum enclosure envelope check contradicts" in inconsistency
        for inconsistency in verification["inconsistencies"]
    )


def test_repeat_has_same_geometry_and_source_identity(tmp_path, accepted_package):
    _, first = accepted_package
    second = acceptance.build_acceptance(
        "designs/calibration/pico2-enclosure-fit.json", tmp_path, "repeat-test"
    )
    assert first["design"]["sha256"] == second["design"]["sha256"]
    assert first["dimensions_mm"] == second["dimensions_mm"]

    def without_export_hashes(checks):
        normalized = json.loads(json.dumps(checks))
        for check in normalized:
            if check["code"] == "export_artifact_integrity":
                for artifact in check["exports"].values():
                    del artifact["sha256"]
                    del artifact["size_bytes"]
        return normalized

    assert without_export_hashes(first["checks"]) == without_export_hashes(
        second["checks"]
    )
    assert first["sources"] == second["sources"]


def test_invalid_design_writes_reason_and_no_exports(tmp_path):
    document = json.loads(open("designs/calibration/pico2-enclosure-fit.json").read())
    document["parameters"]["corner_radius_mm"] = 100
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps(document))
    folder = tmp_path / "result"
    report = acceptance.build_acceptance(source, folder, "invalid-test")
    assert report["digital_status"] == "REVISION_REQUIRED"
    assert "corner_radius_mm" in report["checks"][0]["message"]
    assert (folder / "report.json").exists()
    assert not list(folder.glob("*.step"))


def test_robustness_report_compares_explicit_variant_to_baseline(tmp_path):
    output = tmp_path / "robustness"
    report = acceptance.build_robustness_report(
        "designs/calibration/pico2-enclosure-fit.json",
        output,
        "lid_clearance_mm",
        [0.35, -0.1],
    )
    assert report["analysis"] == "DIGITAL_PARAMETER_VARIATION"
    assert report["tested_values"] == [0.25, 0.35, -0.1]
    assert "no printer or physical tolerance is modeled" in report["scope"]
    assert [case["value"] for case in report["cases"]] == [0.25, 0.35, -0.1]
    assert all(
        "checks" in case and "changed_checks" in case for case in report["cases"]
    )
    changed_measurements = [
        (item["check"], measurement)
        for item in report["cases"][1]["changed_checks"]
        for measurement in item["changed_measurements"]
    ]
    body_width = next(
        measurement
        for check, measurement in changed_measurements
        if check.startswith("export_artifact_integrity:body:")
        and measurement["measurement"] == "source_dimensions_mm[0]"
    )
    assert body_width["baseline"] == pytest.approx(35.9022, abs=0.001)
    assert body_width["variant"] == pytest.approx(36.1022, abs=0.001)
    assert body_width["delta"] == pytest.approx(0.2)
    assert report["cases"][2]["digital_status"] == "REVISION_REQUIRED"
    assert "input_or_geometry::000" in report["cases"][2]["checks"]
    assert all(
        not measurement["measurement"].startswith("exports.")
        for _, measurement in changed_measurements
    )
    assert (output / "robustness.json").is_file()
    summary = (output / "report.md").read_text()
    assert "printer accuracy" in summary
    assert "0.35" in summary
    assert "Δ +0.2000 mm" in summary
    assert "source width" in summary
    assert "round_trip_tolerance" not in summary
    assert "Δ +0.0000" not in summary
    assert "input_or_geometry: status ABSENT → FAIL" in summary


def test_robustness_rejects_duplicate_variants(tmp_path):
    with pytest.raises(ValueError, match="unique"):
        acceptance.build_robustness_report(
            "designs/calibration/pico2-enclosure-fit.json",
            tmp_path / "robustness",
            "lid_clearance_mm",
            [0.3, 0.3],
        )


def test_malformed_export_is_recorded_and_rejected(monkeypatch, tmp_path, capsys):
    original = cq.exporters.export

    def malformed(model, filename, *args, **kwargs):
        result = original(model, filename, *args, **kwargs)
        if str(filename).endswith("body.stl"):
            from pathlib import Path

            Path(filename).write_bytes(b"invalid STL")
        return result

    monkeypatch.setattr(cq.exporters, "export", malformed)
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-enclosure-fit.json", tmp_path, "bad-stl"
    )
    body = next(
        check
        for check in report["checks"]
        if check["code"] == "export_artifact_integrity" and check["subject"] == "body"
    )
    assert body["status"] == "FAIL"
    assert body["exports"]["stl"]["size_bytes"] == len(b"invalid STL")
    assert body["exports"]["stl"]["error"]
    assert report["digital_status"] == "REVISION_REQUIRED"
    verification = acceptance.verify_acceptance(tmp_path)
    assert verification["package_integrity"] == "PASS"
    assert verification["report_consistency"] == "PASS"
    assert verification["acceptance_outcome"] == "REVISION_REQUIRED"
    acceptance.run_acceptance_verify([str(tmp_path)])
    cli_result = json.loads(capsys.readouterr().out)
    assert cli_result["package_integrity"] == "PASS"
    assert cli_result["report_consistency"] == "PASS"
    assert cli_result["acceptance_outcome"] == "REVISION_REQUIRED"


def test_missing_export_is_recorded_and_rejected(monkeypatch, tmp_path):
    original = cq.exporters.export

    def incomplete(model, filename, *args, **kwargs):
        if str(filename).endswith("body.step"):
            raise RuntimeError("simulated exporter failure")
        return original(model, filename, *args, **kwargs)

    monkeypatch.setattr(cq.exporters, "export", incomplete)
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-enclosure-fit.json", tmp_path, "missing-step"
    )
    body = next(
        check
        for check in report["checks"]
        if check["code"] == "export_artifact_integrity" and check["subject"] == "body"
    )
    assert body["status"] == "FAIL"
    assert body["exports"]["step"]["size_bytes"] == 0
    assert body["exports"]["step"]["sha256"] is None
    assert "Exporter raised RuntimeError" in body["exports"]["step"]["error"]
    assert report["digital_status"] == "REVISION_REQUIRED"


def test_blocked_window_is_rejected(monkeypatch, tmp_path):
    original = acceptance.build_pico2_enclosure_fit

    def obstructed(parameters):
        parts = original(parameters)
        # Fill the actual display opening; the result remains one valid solid.
        plug = (
            cq.Workplane("XY")
            .box(24, 13, parameters.lid_thickness_mm, centered=(True, True, False))
            .translate((0, 6, parameters.lid_lip_height_mm))
        )
        parts["lid"] = parts["lid"].union(plug)
        return parts

    monkeypatch.setattr(acceptance, "build_pico2_enclosure_fit", obstructed)
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-enclosure-fit.json", tmp_path, "blocked-window"
    )
    assert report["digital_status"] == "REVISION_REQUIRED"
    assert any(
        check["code"] == "display_window_opening" and check["status"] == "FAIL"
        for check in report["checks"]
    )
    assert not list(tmp_path.glob("*.step"))


def test_source_drift_rejects_run(monkeypatch, tmp_path):
    states = iter(
        [
            {"product": {"head": "before"}, "core": {"head": "core"}},
            {"product": {"head": "after"}, "core": {"head": "core"}},
        ]
    )
    monkeypatch.setattr(acceptance, "_sources", lambda: next(states))
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-enclosure-fit.json", tmp_path, "drift-test"
    )
    assert report["digital_status"] == "REVISION_REQUIRED"
    source_stability = next(
        check for check in report["checks"] if check["code"] == "source_stability"
    )
    assert source_stability["status"] == "FAIL"


def test_verifier_detects_tampering(tmp_path, accepted_package):
    import shutil

    folder, _ = accepted_package
    copied = tmp_path / "copied"
    shutil.copytree(folder, copied)
    (copied / "body.stl").write_text("modified")
    result = acceptance.verify_acceptance(copied)
    assert result["package_integrity"] == "FAIL"
    assert result["acceptance_outcome"] == "DIGITAL_CHECKS_PASSED"
    assert result["changed_or_missing"] == ["body.stl"]


@pytest.mark.parametrize(
    "inconsistency",
    ["failed_check", "export_hash", "profile_inventory", "stl_geometry"],
)
def test_verifier_detects_report_inconsistency(
    tmp_path, accepted_package, inconsistency
):
    import shutil

    folder, _ = accepted_package
    copied = tmp_path / inconsistency
    shutil.copytree(folder, copied)
    report_path = copied / "report.json"
    report = json.loads(report_path.read_text())
    if inconsistency == "failed_check":
        report["checks"][0]["status"] = "FAIL"
    elif inconsistency == "export_hash":
        export_check = next(
            check
            for check in report["checks"]
            if check["code"] == "export_artifact_integrity"
            and check["subject"] == "body"
        )
        export_check["exports"]["stl"]["sha256"] = "0" * 64
    elif inconsistency == "stl_geometry":
        export_check = next(
            check
            for check in report["checks"]
            if check["code"] == "export_artifact_integrity"
            and check["subject"] == "body"
        )
        export_check["exports"]["stl"]["geometry_comparison"][
            "mismatching_samples"
        ] += 1
    else:
        del report["artifacts"]["acceptance-profile.json"]
    report_path.write_text(json.dumps(report))

    result = acceptance.verify_acceptance(copied)
    assert result["package_integrity"] == "PASS"
    assert result["report_consistency"] == "FAIL"
    assert result["acceptance_outcome"] == "DIGITAL_CHECKS_PASSED"
    with pytest.raises(SystemExit, match="1"):
        acceptance.run_acceptance_verify([str(copied)])


def test_trusted_report_hash_mismatch_fails_authenticity(tmp_path, accepted_package):
    folder, _ = accepted_package
    report_sha256 = acceptance.verify_acceptance(folder)["report_sha256"]
    mismatched = ("0" if report_sha256[0] != "0" else "1") + report_sha256[1:]
    result = acceptance.verify_acceptance(folder, expected_report_sha256=mismatched)
    assert result["package_integrity"] == "PASS"
    assert result["report_consistency"] == "PASS"
    assert result["authenticity"] == "TRUSTED_SHA256_MISMATCH"
    with pytest.raises(SystemExit, match="1"):
        acceptance.run_acceptance_verify(
            [str(folder), "--trusted-report-sha256", mismatched]
        )


def test_trusted_report_hash_requires_sha256_hex(tmp_path, accepted_package):
    folder, _ = accepted_package
    with pytest.raises(ValueError, match="64 hexadecimal"):
        acceptance.verify_acceptance(folder, expected_report_sha256="not-a-hash")


def test_never_overwrites_existing_revision(accepted_package):
    folder, _ = accepted_package
    with pytest.raises(ValueError, match="empty directory"):
        acceptance.build_acceptance(
            "designs/calibration/pico2-enclosure-fit.json", folder, "overwrite"
        )


@pytest.mark.parametrize("design", ["reference", "synthetic"])
def test_explicit_retention_passes_six_stops_and_clearance(tmp_path, design):
    report = acceptance.build_acceptance(
        f"designs/calibration/pico2-oled-clips-{design}.json",
        tmp_path,
        f"retained-{design}",
    )
    assert report["digital_status"] == (
        "DIGITAL_CHECKS_PASSED" if design == "reference" else "REVISION_REQUIRED"
    )
    retention = next(
        check for check in report["checks"] if check["code"] == "oled_retention"
    )
    assert retention["status"] == "PASS"
    assert len(retention["probes"]) == 6
    assert all(probe["stop_intersection_mm3"] > 1e-6 for probe in retention["probes"])
    physical = next(
        check
        for check in report["checks"]
        if check["code"] == "clip_flex_and_holding_strength"
    )
    assert physical["status"] == "NOT_CHECKED"
    assert report["physical_status"] == "PENDING"
    if design == "synthetic":
        envelope = next(
            check
            for check in report["checks"]
            if check["code"] == "maximum_enclosure_envelope"
        )
        assert envelope["exceeded_dimensions"] == ["width", "height"]


def test_missing_clips_cannot_claim_retention(monkeypatch, tmp_path):
    import zcad.generators.calibration.pico2_enclosure_fit as generator

    monkeypatch.setattr(
        generator, "add_display_retainer", lambda model, *, parameters: model
    )
    report = acceptance.build_acceptance(
        "designs/calibration/pico2-oled-clips-reference.json", tmp_path, "missing-clips"
    )
    retention = next(
        check for check in report["checks"] if check["code"] == "oled_retention"
    )
    assert retention["status"] == "FAIL"
    assert (
        next(
            probe for probe in retention["probes"] if probe["direction"] == "negative_z"
        )["status"]
        == "FAIL"
    )
    assert report["digital_status"] == "REVISION_REQUIRED"
    assert not list(tmp_path.glob("*.step"))
