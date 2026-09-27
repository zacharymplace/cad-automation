"""Thin membranes must be caught in the actual staged STL before publication."""

import json
from pathlib import Path

import cadquery as cq
import pytest
from zcad_core.exporters import ExportRequest, export_parts
from zcad_core.validation.design_report import DesignValidationError
from zcad_core.validation.stl_mesh import read_stl

from zcad.feature_validation import feature_checks
from zcad.generators.tolerance_coupon import (
    ToleranceCouponParameters,
    build_tolerance_coupon,
)
from zcad.stl_features import stl_feature_checks


@pytest.fixture(scope="module")
def coupon():
    return build_tolerance_coupon(ToleranceCouponParameters([3.0], [3.0]))


@pytest.mark.parametrize("kind,y", [("hole", 9), ("slot", -9)])
@pytest.mark.parametrize("z", [-1.9, -0.7, 0.7, 1.9])
def test_staged_thin_membrane_blocks_export(tmp_path, monkeypatch, coupon, kind, y, z):
    original = cq.exporters.export
    damaged = coupon.union(cq.Workplane().box(4, 14, 0.02).translate((0, y, z))).val()

    def corrupt(shape, path, *args, **kwargs):
        original(
            damaged if str(path).endswith(".stl") else shape, path, *args, **kwargs
        )
        if str(path).endswith(".stl"):
            mesh = read_stl(Path(path).read_bytes())[0]
            assert all(not mesh.contains((0, y, height)) for height in (-1.6, 0, 1.6))

    out = tmp_path / "exports"
    out.mkdir()
    (out / "coupon.stl").write_bytes(b"prior")
    monkeypatch.setattr(cq.exporters, "export", corrupt)
    with pytest.raises(DesignValidationError) as caught:
        export_parts(
            ExportRequest(
                design_name="coupon",
                design_type="tolerance_coupon",
                parts={"main": coupon},
                parameters={"hole_diameters": [3.0], "slot_widths": [3.0]},
                output_directory=out,
                repository_root=tmp_path,
                feature_validator=feature_checks,
                stl_feature_validator=stl_feature_checks,
            )
        )
    checks = caught.value.report["stl_round_trip"]["checks"]
    check = next(
        c
        for c in checks
        if c.get("feature_id") == kind + "_01"
        and c["code"] == "stl_coupon_opening_vertical_clearance"
    )
    assert check["status"] == "FAIL"
    assert any(p["surface_contact_count"] for p in check["probes"])
    assert {p.name: p.read_bytes() for p in out.iterdir()} == {"coupon.stl": b"prior"}


def test_nominal_report_records_full_depth(tmp_path, coupon):
    path = tmp_path / "coupon.stl"
    cq.exporters.export(coupon, str(path))
    mesh = read_stl(path.read_bytes())[0]
    checks = stl_feature_checks(
        design_type="tolerance_coupon",
        parts={"main": mesh},
        parameters={"hole_diameters": [3.0], "slot_widths": [3.0]},
    )
    assert all(c["status"] == "PASS" for c in checks)
    opening = [c for c in checks if "vertical_clearance" in c["code"]]
    assert len(opening) == 2
    assert all(c["z_interval_mm"] == [-2, 2] for c in opening)
    assert [c["sample_count"] for c in opening] == [17, 23]
    json.dumps(checks, allow_nan=False)
