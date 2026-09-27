"""Geometric label-footprint checks for the two catalog calibration designs."""

import json
from pathlib import Path

import cadquery as cq
import pytest

from zcad.generators import tolerance_coupon as coupon

DESIGNS = Path(__file__).parents[1] / "designs" / "calibration"


def text_bounds(text, size, height, x=0, y=0):
    return (
        cq.Workplane("XY")
        .center(x, y)
        .text(text, size, height, halign="center", valign="center")
        .val()
        .BoundingBox()
    )


def test_catalog_coupon_labels_clear_openings_and_edges(monkeypatch):
    values = json.loads((DESIGNS / "default-tolerance-coupon.json").read_text())[
        "parameters"
    ]
    parameters = coupon.ToleranceCouponParameters(**values)
    labels = []
    original = coupon.add_embossed_label

    def capture(model, **kwargs):
        labels.append(
            text_bounds(
                kwargs["text"],
                kwargs["text_size"],
                kwargs["emboss_height"],
                kwargs["x"],
                kwargs["y"],
            )
        )
        return original(model, **kwargs)

    monkeypatch.setattr(coupon, "add_embossed_label", capture)
    model = coupon.build_tolerance_coupon(parameters)
    assert model.val().isValid()
    assert len(model.val().Solids()) == 1
    assert len(labels) == 10
    bounds = model.val().BoundingBox()
    assert (bounds.xlen, bounds.ylen) == pytest.approx((100, 46))
    # Use conservative rectangular keepouts enclosing each circular/slot opening.
    openings = []
    for i, diameter in enumerate(parameters.hole_diameters):
        x = -36 + i * 18
        openings.append(
            (x - diameter / 2, x + diameter / 2, 9 - diameter / 2, 9 + diameter / 2)
        )
    for i, width in enumerate(parameters.slot_widths):
        x = -36 + i * 18
        openings.append((x - width / 2, x + width / 2, -9 - 11.7 / 2, -9 + 11.7 / 2))
    for label in labels:
        # Central rectangular region avoids the plate's rounded corners.
        assert -47 < label.xmin < label.xmax < 47
        assert -20 < label.ymin < label.ymax < 20
        for xmin, xmax, ymin, ymax in openings:
            assert (
                label.xmax + 0.5 < xmin
                or label.xmin - 0.5 > xmax
                or label.ymax + 0.5 < ymin
                or label.ymin - 0.5 > ymax
            )
    for i, a in enumerate(labels):
        for b in labels[i + 1 :]:
            assert (
                a.xmax < b.xmin or a.xmin > b.xmax or a.ymax < b.ymin or a.ymin > b.ymax
            )


def test_catalog_enclosure_label_within_flat_lid_surface():
    p = json.loads((DESIGNS / "enclosure-fit-test.json").read_text())["parameters"]
    b = text_bounds(p["label"], p["label_size"], p["label_height"])
    assert max(abs(b.xmin), abs(b.xmax)) < p["width"] / 2 - p["corner_radius"] - 1
    assert max(abs(b.ymin), abs(b.ymax)) < p["depth"] / 2 - p["corner_radius"] - 1
