import cadquery as cq
import pytest

from zcad.generators.garden_insertion import insertion_plan, vertical_sweep
from zcad.generators.pixel_garden_assembly import build_garden_assembly


def instance(name, z):
    return {"name": name, "position_mm": [0, 0, z]}


def test_continuous_sweep_volume():
    box = cq.Workplane("XY").box(2, 3, 4).val()
    sweep = vertical_sweep(box, 5)
    assert sweep.isValid()
    assert sweep.Volume() == pytest.approx(2 * 3 * 9)
    # A thin obstruction strictly between endpoints must still be detected.
    thin = cq.Workplane("XY").box(1, 1, 0.01).translate((0, 0, 2.7)).val()
    assert box.intersect(thin).Volume() == pytest.approx(0)
    assert box.translate((0, 0, 5)).intersect(thin).Volume() == pytest.approx(0)
    assert sweep.intersect(thin).Volume() == pytest.approx(0.01)


def test_blocking_requires_lower_first():
    box = cq.Workplane("XY").box(2, 2, 2).val()
    report = insertion_plan(box, [instance("upper", 3), instance("lower", 0)])
    assert report["status"] == "PASS"
    assert report["assembly_order"] == ["lower", "upper"]
    assert [(m["moving"], m["blocked_by"]) for m in report["blocked_moves"]] == [
        ("lower", "upper")
    ]


def test_cyclic_blocking_has_no_complete_order():
    # Two disconnected slabs model a synthetic obstruction fixture. Their
    # interleaved final positions are clear, but both upward sweeps interfere.
    box = cq.Workplane("XY").box(2, 2, 1).val()
    fixture = cq.Compound.makeCompound([box, box.translate((0, 0, 6))])
    assert fixture.intersect(fixture.translate((0, 0, 3))).Volume() == pytest.approx(0)
    report = insertion_plan(fixture, [instance("a", 0), instance("b", 3)])
    assert report["status"] == "BLOCKED"
    assert report["assembly_order"] == []
    assert report["unresolved"] == ["a", "b"]
    assert len(report["blocked_moves"]) == 2


@pytest.mark.parametrize("pattern", [["X"], ["XX", "XX"], ["XXX", "X.X", "XXX"]])
def test_real_garden_orders(pattern):
    _, report = build_garden_assembly({"pattern": pattern})
    check = report["insertion_check"]
    assert check["status"] == "PASS"
    assert check["blocked_moves"] == []
    assert set(check["assembly_order"]) == {i["name"] for i in report["instances"]}


@pytest.mark.parametrize("lift", [0, -1, float("nan"), float("inf")])
def test_invalid_lift(lift):
    with pytest.raises(ValueError):
        vertical_sweep(cq.Workplane().box(1, 1, 1).val(), lift)
