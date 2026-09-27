from xml.etree import ElementTree as ET

import pytest

from zcad.generators.garden_preview import assembly_preview_svg
from zcad.generators.pixel_garden_assembly import build_garden_assembly

NS = {"s": "http://www.w3.org/2000/svg"}


@pytest.mark.parametrize(
    "pattern,pairs,exposed",
    [
        (["X"], 0, 4),
        (["XX"], 1, 6),
        (["X", "X"], 1, 6),
        (["XXX", "X.X", "XXX"], 8, 16),
    ],
)
def test_connector_mapping(pattern, pairs, exposed):
    _, report = build_garden_assembly({"pattern": pattern})
    svg = ET.fromstring(assembly_preview_svg(report))
    groups = svg.findall("s:g", NS)
    connectors = [c for g in groups for c in g.findall("s:g", NS)]
    assert len(connectors) == 4 * report["module_count"]
    assert sum(c.get("data-state") == "exposed" for c in connectors) == exposed
    assert len(svg.findall("s:line", NS)) == pairs
    for g in groups:
        sides = {c.get("data-side"): c for c in g.findall("s:g", NS)}
        assert sides["+X"].get("data-kind") == "male"
        assert sides["+Y"].get("data-kind") == "male"
        assert sides["-X"].get("data-kind") == "female"
        assert sides["-Y"].get("data-kind") == "female"
        assert "rotate(-90)" in sides["+Y"].get("transform")
        assert "rotate(90)" in sides["-Y"].get("transform")
    by_name = {g.get("data-module"): g for g in groups}
    for connection in report["connections"]:
        for role, sign, other in (("male", "+", "female"), ("female", "-", "male")):
            g = by_name[connection[role]]
            c = next(
                c
                for c in g.findall("s:g", NS)
                if c.get("data-side") == sign + connection["axis"]
            )
            assert c.get("data-mate") == connection[other]
            assert c.get("data-state") == "connected"


@pytest.mark.parametrize("change", ["missing", "duplicate", "reverse", "count"])
def test_inconsistent_connections_rejected(change):
    _, report = build_garden_assembly({"pattern": ["XX"]})
    if change == "missing":
        report["connections"] = []
    elif change == "duplicate":
        report["connections"] *= 2
    elif change == "reverse":
        c = report["connections"][0]
        c["male"], c["female"] = c["female"], c["male"]
    else:
        report["connection_count"] = 0
    with pytest.raises(ValueError, match="Connections"):
        assembly_preview_svg(report)
