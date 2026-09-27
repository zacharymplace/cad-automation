import json
from pathlib import Path

import cadquery as cq
import pytest

from zcad.catalog_validation import run_catalog
from zcad.feature_validation import validate_design
from zcad.generators.tolerance_coupon import (
    ToleranceCouponParameters,
    build_tolerance_coupon,
)
from zcad.validation_cli import run_validation


@pytest.fixture(scope="module")
def coupon():
    data = json.loads(
        (
            Path(__file__).parents[1]
            / "designs/calibration/default-tolerance-coupon.json"
        ).read_text()
    )
    return data, build_tolerance_coupon(ToleranceCouponParameters(**data["parameters"]))


def report(data, model):
    return validate_design(
        design_name=data["name"],
        design_type=data["type"],
        parameters=data["parameters"],
        parts={"main": model},
    )


def openings(result):
    return [c for c in result["checks"] if c["code"] == "coupon_opening_clearance"]


def test_real_coupon_clear(coupon):
    data, model = coupon
    checks = openings(report(data, model))
    assert len(checks) == 10
    assert all(c["status"] == "PASS" for c in checks)
    assert len({c["feature_id"] for c in checks}) == 10


@pytest.mark.parametrize("kind", ["hole", "slot"])
@pytest.mark.parametrize("height,z", [(2, -1), (0.02, 0.37), (4, 0)])
def test_obstructions_detected(coupon, kind, height, z):
    data, model = coupon
    y = 9 if kind == "hole" else -9
    obstruction = cq.Workplane().box(2, 2, height).translate((-36, y, z))
    # Separate stack item exercises inspection of all solids, not just val().
    broken = cq.Workplane().newObject([model.val(), obstruction.val()])
    result = report(data, broken)
    failed = [c for c in openings(result) if c["status"] == "FAIL"]
    assert [c["feature_id"] for c in failed] == [kind + "_01"]
    assert failed[0]["residual_material_mm3"] > 0
    assert result["evaluated_status"] == "FAIL"


def test_missing_openings(coupon):
    data, _ = coupon
    checks = openings(report(data, cq.Workplane().box(100, 46, 4)))
    assert len(checks) == 10
    assert all(c["status"] == "FAIL" for c in checks)


def test_cli_and_catalog_reject_obstruction(coupon, tmp_path, capsys):
    data, _ = coupon
    deps = dict(
        read_design=lambda p: data,
        generate_parts=lambda d: {"main": cq.Workplane().box(100, 46, 4)},
        load_printer_profile=lambda p: None,
    )
    with pytest.raises(SystemExit) as caught:
        run_validation(["coupon.json", "--json"], **deps)
    assert caught.value.code == 1
    assert json.loads(capsys.readouterr().out)["policy_result"]["status"] == "FAIL"
    catalog, policy = tmp_path / "catalog.json", tmp_path / "policy.json"
    catalog.write_text(
        json.dumps({"schema_version": "1.0", "designs": ["coupon.json"]})
    )
    policy.write_text(
        json.dumps(
            {"schema_version": "1.0", "required_checks": [], "fail_on_warnings": False}
        )
    )
    with pytest.raises(SystemExit) as caught:
        run_catalog([str(catalog), "--policy", str(policy), "--json"], **deps)
    assert caught.value.code == 1
    assert json.loads(capsys.readouterr().out)["counts"]["FAIL"] == 1


def test_unsupported_not_claimed():
    result = validate_design(
        design_name="other",
        design_type="other",
        parts={"main": cq.Workplane().box(2, 2, 2)},
    )
    assert openings(result)[0]["status"] == "NOT_CHECKED"


def test_intersection_error_fails_closed(coupon, monkeypatch):
    data, model = coupon

    def broken(*args, **kwargs):
        raise RuntimeError("kernel fixture")

    monkeypatch.setattr(cq.Solid, "intersect", broken)
    result = report(data, model)
    assert result["evaluated_status"] == "FAIL"
    assert openings(result)[0]["status"] == "FAIL"
    assert "kernel fixture" in openings(result)[0]["message"]
