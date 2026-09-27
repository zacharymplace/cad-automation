"""STEP feature evidence must describe the actual published bytes."""

import hashlib
import json
from dataclasses import replace

import cadquery as cq
import pytest
from zcad_core.exporters import ExportRequest, export_parts
from zcad_core.validation.design_report import DesignValidationError

from zcad.feature_validation import feature_checks
from zcad.generators.tolerance_coupon import (
    ToleranceCouponParameters,
    build_tolerance_coupon,
)


@pytest.fixture(scope="module")
def coupon():
    return build_tolerance_coupon(ToleranceCouponParameters([3.0], [3.0]))


def request(tmp_path, coupon):
    return ExportRequest(
        "coupon",
        "tolerance_coupon",
        {"main": coupon},
        tmp_path / "out",
        tmp_path,
        parameters={"hole_diameters": [3.0], "slot_widths": [3.0]},
        feature_validator=feature_checks,
    )


def test_published_step_passes_and_matches_recorded_hash(tmp_path, coupon):
    result = export_parts(request(tmp_path, coupon))
    evidence = result.validation_report["step_round_trip"]
    assert evidence["status"] == "PASS"
    assert len(evidence["checks"]) == 4
    assert all(c["status"] == "PASS" for c in evidence["checks"])
    part = result.parts[0]
    assert (
        evidence["step_sha256_by_part"]["main"]
        == hashlib.sha256(part.step_path.read_bytes()).hexdigest()
    )
    assert (
        json.loads(part.metadata_path.read_text())["design_validation"][
            "step_round_trip"
        ]
        == evidence
    )


@pytest.mark.parametrize("fault", ["blocked", "oversized", "unreadable"])
@pytest.mark.parametrize("existing", [False, True])
def test_bad_step_is_not_published(tmp_path, coupon, monkeypatch, fault, existing):
    req = request(tmp_path, coupon)
    if existing:
        req.output_directory.mkdir()
        (req.output_directory / "coupon.step").write_bytes(b"prior")
    original = cq.exporters.export

    def corrupt(model, filename, *args, **kwargs):
        if filename.endswith(".step"):
            if fault == "unreadable":
                from pathlib import Path

                Path(filename).write_bytes(b"invalid STEP")
                return
            if fault == "blocked":
                model = coupon.union(cq.Workplane().box(3, 3, 0.1).translate((0, 9, 0)))
            else:
                model = coupon.cut(
                    cq.Workplane()
                    .circle(1.6)
                    .extrude(4, both=True)
                    .translate((0, 9, 0))
                )
        return original(model, filename, *args, **kwargs)

    monkeypatch.setattr(cq.exporters, "export", corrupt)
    with pytest.raises(DesignValidationError) as error:
        export_parts(req)
    assert error.value.report["step_round_trip"]["status"] == "FAIL"
    if existing:
        assert {p.name: p.read_bytes() for p in req.output_directory.iterdir()} == {
            "coupon.step": b"prior"
        }
    else:
        assert not req.output_directory.exists()


def test_nonapplicable_does_not_claim_feature_pass(tmp_path):
    req = request(tmp_path, cq.Workplane().box(2, 3, 4))
    result = export_parts(replace(req, design_type="box", parameters={}))
    assert result.validation_report["step_round_trip"]["status"] == "NOT_CHECKED"
