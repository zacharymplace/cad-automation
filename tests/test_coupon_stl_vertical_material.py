"""Gaps in the emitted mesh must fail before replacing an export set."""

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
@pytest.mark.parametrize("height", [-1.9, -0.7, 0.7, 1.9])
def test_thin_mesh_gap_rejected(tmp_path, monkeypatch, coupon, kind, y, height):
    original = cq.exporters.export
    damaged = coupon.cut(cq.Workplane().box(6, 16, 0.02).translate((0, y, height)))

    def corrupt(shape, path, *args, **kwargs):
        original(
            damaged if str(path).endswith(".stl") else shape, path, *args, **kwargs
        )
        if str(path).endswith(".stl"):
            model = read_stl(Path(path).read_bytes())[0]
            assert all(model.contains((1.6, y, z)) for z in (-1.6, 0, 1.6))

    output = tmp_path / "exports"
    output.mkdir()
    (output / "coupon.stl").write_bytes(b"prior")
    monkeypatch.setattr(cq.exporters, "export", corrupt)
    with pytest.raises(DesignValidationError) as caught:
        export_parts(
            ExportRequest(
                design_name="coupon",
                design_type="tolerance_coupon",
                parts={"main": coupon},
                parameters={"hole_diameters": [3.0], "slot_widths": [3.0]},
                output_directory=output,
                repository_root=tmp_path,
                feature_validator=feature_checks,
                stl_feature_validator=stl_feature_checks,
            )
        )
    checks = caught.value.report["stl_round_trip"]["checks"]
    failure = next(
        c
        for c in checks
        if c["code"] == "stl_coupon_material_vertical_coverage"
        and c["feature_id"] == kind + "_01"
    )
    assert failure["status"] == "FAIL"
    assert any(p["interior_contact_count"] for p in failure["probes"])
    assert {p.name: p.read_bytes() for p in output.iterdir()} == {
        "coupon.stl": b"prior"
    }


def test_nominal_material_report(tmp_path, coupon):
    path = tmp_path / "coupon.stl"
    cq.exporters.export(coupon, str(path))
    model = read_stl(path.read_bytes())[0]
    checks = stl_feature_checks(
        design_type="tolerance_coupon",
        parts={"main": model},
        parameters={"hole_diameters": [3.0], "slot_widths": [3.0]},
    )
    assert all(c["status"] == "PASS" for c in checks)
    material = [
        c for c in checks if c["code"] == "stl_coupon_material_vertical_coverage"
    ]
    assert [c["sample_count"] for c in material] == [16, 22]
    assert all(c["z_interval_mm"] == [-2, 2] for c in material)
    assert all(p["midpoint_occupied"] for c in material for p in c["probes"])
    json.dumps(checks, allow_nan=False)
