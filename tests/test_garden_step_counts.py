import re
from xml.etree.ElementTree import fromstring

from zcad.generators.garden_steps import assembly_steps_html
from zcad.generators.pixel_garden_assembly import build_garden_assembly


def counts(report):
    html = assembly_steps_html(report).replace(" hidden>", ' hidden="hidden">')
    return [
        {n.get("data-count"): int(n.text) for n in fromstring(s).iter("dd")}
        for s in re.findall(r"<section.*?</section>", html)
    ]


def test_ring_counts_and_connector_conservation():
    _, report = build_garden_assembly({"pattern": ["XXX", "X.X", "XXX"]})
    frames = counts(report)
    assert [f["engaged"] for f in frames] == [0, 0, 1, 2, 3, 4, 5, 6, 8]
    assert [f["next"] for f in frames] == [0, 1, 1, 1, 1, 1, 1, 2, 0]
    assert [f["waiting"] for f in frames] == [0, 2, 2, 2, 2, 2, 2, 2, 0]
    for installed, frame in enumerate(frames):
        assert (
            2 * frame["engaged"] + frame["waiting"] + frame["exposed"] == 4 * installed
        )
    assert frames[-1] == {"engaged": 8, "next": 0, "waiting": 0, "exposed": 16}


def test_reverse_order_and_single_module():
    _, report = build_garden_assembly({"pattern": ["XXX"]})
    # Install both ends before the middle; counts must follow the report order.
    a, b, c = report["insertion_check"]["assembly_order"]
    report["insertion_check"]["assembly_order"] = [c, a, b]
    assert counts(report)[2] == {"engaged": 0, "next": 2, "waiting": 2, "exposed": 6}
    _, single = build_garden_assembly({"pattern": ["X"]})
    assert counts(single) == [
        {"engaged": 0, "next": 0, "waiting": 0, "exposed": 0},
        {"engaged": 0, "next": 0, "waiting": 0, "exposed": 4},
    ]


def test_blocked_does_not_claim_step_counts():
    _, report = build_garden_assembly({"pattern": ["X"]})
    report["insertion_check"] = {"status": "BLOCKED", "assembly_order": []}
    assert counts(report) == [{}]
