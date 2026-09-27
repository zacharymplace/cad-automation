"""Export must preserve the same feature evidence and reject bad geometry."""

import ast
import json
from pathlib import Path

import cadquery as cq
import pytest
from zcad_core.exporters import ExportRequest, export_parts
from zcad_core.validation.design_report import DesignValidationError

from zcad.feature_validation import feature_checks, validate_design
from zcad.generators.tolerance_coupon import (
    ToleranceCouponParameters,
    build_tolerance_coupon,
)


@pytest.fixture(scope="module")
def coupon():
    return build_tolerance_coupon(ToleranceCouponParameters([3.0], [3.0]))


def request(tmp_path, model):
    return ExportRequest(
        design_name="coupon",
        design_type="tolerance_coupon",
        parts={"main": model},
        parameters={"hole_diameters": [3.0], "slot_widths": [3.0]},
        output_directory=tmp_path / "exports",
        repository_root=tmp_path,
        feature_validator=feature_checks,
    )


def test_export_records_shared_checks(tmp_path, coupon):
    req = request(tmp_path, coupon)
    result = export_parts(req)
    report = validate_design(
        design_name=req.design_name,
        design_type=req.design_type,
        parts=req.parts,
        parameters=req.parameters,
    )
    expected = [c for c in report["checks"] if c["code"].startswith("coupon_")]
    actual = [
        c for c in result.validation_report["checks"] if c["code"].startswith("coupon_")
    ]
    assert actual == expected
    assert len(actual) == 4
    assert all(c["status"] == "PASS" for c in actual)
    metadata = json.loads(result.parts[0].metadata_path.read_text())
    assert metadata["design_validation"] == result.validation_report


@pytest.mark.parametrize("damage", ["blocked", "oversized", "displaced"])
@pytest.mark.parametrize("existing", [False, True])
def test_failure_preserves_outputs(tmp_path, coupon, damage, existing):
    if damage == "blocked":
        model = coupon.union(cq.Workplane().box(3, 3, 0.1).translate((0, 9, 0)))
    elif damage == "oversized":
        model = coupon.cut(
            cq.Workplane().circle(1.6).extrude(4, both=True).translate((0, 9, 0))
        )
    else:
        model = coupon.translate((100, 0, 0))
    req = request(tmp_path, model)
    if existing:
        req.output_directory.mkdir()
        (req.output_directory / "coupon.step").write_bytes(b"prior artifact")
    with pytest.raises(DesignValidationError):
        export_parts(req)
    if existing:
        assert {p.name: p.read_bytes() for p in req.output_directory.iterdir()} == {
            "coupon.step": b"prior artifact"
        }
    else:
        assert not req.output_directory.exists()


def test_both_cli_export_requests_register_checks():
    tree = ast.parse((Path(__file__).parents[1] / "src/zcad/cli.py").read_text())
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "ExportRequest"
    ]
    assert len(calls) == 2
    assert all(
        any(
            k.arg == "feature_validator"
            and isinstance(k.value, ast.Name)
            and k.value.id == "feature_checks"
            for k in c.keywords
        )
        for c in calls
    )
