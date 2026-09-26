import copy
from xml.etree import ElementTree as ET

import pytest

from zcad.generators.garden_preview import assembly_preview_svg

NS = {"s": "http://www.w3.org/2000/svg"}


def report():
    return {
        "collision_check": {"status": "PASS"},
        "insertion_check": {"status": "PASS", "assembly_order": ["b", "a"]},
        "module_count": 2,
        "pitch_mm": 40,
        "instances": [
            {"name": "a", "row": 0, "column": 0, "position_mm": [0, 40, 0]},
            {"name": "b", "row": 1, "column": 1, "position_mm": [40, 0, 0]},
        ],
    }


def test_numbering_uses_checked_order_and_positions():
    data = report()
    original = copy.deepcopy(data)
    svg = ET.fromstring(assembly_preview_svg(data))
    groups = svg.findall("s:g", NS)
    assert [(g.get("data-module"), g.get("data-step")) for g in groups] == [
        ("a", "2"),
        ("b", "1"),
    ]
    first, second = [g.find("s:rect", NS) for g in groups]
    assert float(first.get("x")) < float(second.get("x"))
    assert float(first.get("y")) < float(second.get("y"))
    assert data == original


def test_blocked_preview_has_no_numbers():
    data = report()
    data["insertion_check"] = {"status": "BLOCKED", "assembly_order": []}
    svg = ET.fromstring(assembly_preview_svg(data))
    assert all(g.get("data-step") == "" for g in svg.findall("s:g", NS))
    assert "BLOCKED — no complete insertion order" in "".join(svg.itertext())


@pytest.mark.parametrize("order", [["a"], ["a", "a"], ["a", "unknown"]])
def test_bad_order_rejected(order):
    data = report()
    data["insertion_check"]["assembly_order"] = order
    with pytest.raises(ValueError):
        assembly_preview_svg(data)


def test_xml_escaping():
    data = report()
    data["instances"][0]["name"] = '<module & "one">'
    data["insertion_check"]["assembly_order"][1] = '<module & "one">'
    svg = ET.fromstring(assembly_preview_svg(data))
    assert svg.find("s:g", NS).get("data-module") == '<module & "one">'


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True])
def test_nonfinite_dimensions_rejected(bad):
    data = report()
    data["instances"][0]["position_mm"][0] = bad
    with pytest.raises(ValueError):
        assembly_preview_svg(data)


def test_unchecked_report_rejected():
    data = report()
    data["collision_check"]["status"] = "FAIL"
    with pytest.raises(ValueError):
        assembly_preview_svg(data)
