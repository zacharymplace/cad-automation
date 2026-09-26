import hashlib
import json
from copy import deepcopy
from xml.etree.ElementTree import fromstring

import pytest

from zcad.generators.garden_steps import assembly_steps_html
from zcad.generators.pixel_garden_assembly import export_garden_assembly


def report():
    return {
        "collision_check": {"status": "PASS"},
        "insertion_check": {"status": "PASS", "assembly_order": ["right", "left"]},
        "module_count": 2,
        "pitch_mm": 40,
        "instances": [
            {"name": "left", "row": 0, "column": 0, "position_mm": [0, 0, 0]},
            {"name": "right", "row": 0, "column": 1, "position_mm": [40, 0, 0]},
        ],
        "connection_count": 1,
        "connections": [{"male": "left", "female": "right", "axis": "X"}],
    }


def sections(html):
    import re

    return [fromstring(s) for s in re.findall(r"<section.*?</section>", html)]


def test_checked_order_frames_and_mates():
    data = report()
    before = deepcopy(data)
    frames = sections(
        assembly_steps_html(data).replace(" hidden>", ' hidden="hidden">')
    )
    assert len(frames) == 3
    states = [
        {
            g.get("data-module"): g.get("data-stage")
            for g in f.iter()
            if g.get("data-module")
        }
        for f in frames
    ]
    assert states == [
        {"left": "pending", "right": "next"},
        {"left": "next", "right": "installed"},
        {"left": "installed", "right": "installed"},
    ]
    assert "Mate with installed: right" in "".join(frames[1].itertext())
    active = [g for g in frames[1].iter() if g.get("data-active-mate")]
    assert {(g.get("data-kind"), g.get("data-side")) for g in active} == {
        ("male", "+X"),
        ("female", "-X"),
    }
    # Numbers and location labels fade with their module, not independently.
    for f in frames:
        for g in f.iter():
            if g.get("data-module"):
                assert len(g.findall("{*}text")) == 2
    assert data == before


def test_blocked_has_no_playback():
    data = report()
    data["insertion_check"] = {"status": "BLOCKED", "assembly_order": []}
    html = assembly_steps_html(data)
    assert 'id="step"' not in html
    assert 'data-frame="1"' not in html
    assert "BLOCKED — no complete assembly sequence" in html


@pytest.mark.parametrize("bad", [[], ["left", "left"], ["left", "unknown"]])
def test_invalid_order_rejected(bad):
    data = report()
    data["insertion_check"]["assembly_order"] = bad
    with pytest.raises(ValueError):
        assembly_steps_html(data)


def test_names_cannot_inject_html():
    data = report()
    evil = '</script><script>alert("oops")</script>'
    data["instances"][0]["name"] = evil
    data["insertion_check"]["assembly_order"][1] = evil
    data["connections"][0]["male"] = evil
    html = assembly_steps_html(data)
    assert evil not in html
    assert html.count("<script>") == 1


def test_export_includes_hashed_steps(tmp_path):
    source = tmp_path / "layout.json"
    source.write_text(json.dumps({"pattern": ["X"]}))
    output = tmp_path / "out"
    result = export_garden_assembly(source, output)
    data = (output / "assembly-steps.html").read_bytes()
    assert (
        result["artifacts"]["assembly-steps.html"] == hashlib.sha256(data).hexdigest()
    )
    assert b"Complete" in data
