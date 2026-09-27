"""Material presence must complement empty-opening evidence."""

import cadquery as cq
import pytest

from zcad.feature_validation import validate_design
from zcad.generators.tolerance_coupon import (
    ToleranceCouponParameters,
    build_tolerance_coupon,
)
from zcad.validation_policy import evaluate_policy, load_policy


@pytest.fixture(scope="module")
def model():
    return build_tolerance_coupon(ToleranceCouponParameters([3.0], [3.0]))


def assess(model):
    return validate_design(
        design_name="coupon",
        design_type="tolerance_coupon",
        parameters={"hole_diameters": [3.0], "slot_widths": [3.0]},
        parts={"main": model},
    )


def material(report):
    return [c for c in report["checks"] if c["code"] == "coupon_surrounding_material"]


def test_nominal_band_present(model):
    checks = material(assess(model))
    assert len(checks) == 2
    assert all(c["status"] == "PASS" for c in checks)


@pytest.mark.parametrize("kind", ["hole", "slot"])
def test_oversized_cut(model, kind):
    plane = cq.Workplane("XY", origin=(0, 9 if kind == "hole" else -9, -2))
    profile = plane.circle(1.6) if kind == "hole" else plane.slot2D(11.9, 3.2, 90)
    report = assess(model.cut(profile.extrude(4)))
    failed = [c for c in material(report) if c["status"] == "FAIL"]
    assert [c["feature_id"] for c in failed] == [kind + "_01"]
    assert failed[0]["missing_material_mm3"] > 0
    assert evaluate_policy(report, load_policy())["status"] == "FAIL"


@pytest.mark.parametrize("move", [(100, 0, 0), (0, 0, 20)])
def test_displaced_part(model, move):
    report = assess(model.translate(move))
    assert all(c["status"] == "FAIL" for c in material(report))


def test_duplicate_solids_cannot_hide_local_missing_material(model):
    notch = cq.Workplane().box(0.4, 0.4, 0.02).translate((1.6, 9, 0.37))
    damaged = model.cut(notch).val()
    report = assess(cq.Workplane().newObject([damaged, damaged.copy()]))
    check = material(report)[0]
    assert check["status"] == "FAIL"
    assert check["missing_material_mm3"] > 0


def test_missing_band_cannot_be_replaced_by_unrelated_volume(model):
    tiny = cq.Workplane().box(1, 1, 1)
    assert all(c["status"] == "FAIL" for c in material(assess(tiny)))
