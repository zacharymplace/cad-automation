"""Numbered schematic generated solely from an assembly check report."""

import math
from numbers import Real
from xml.etree.ElementTree import Element, SubElement, tostring


def assembly_preview_svg(report: dict) -> str:
    """Render checked positions; fail closed on inconsistent step numbering."""
    if report.get("collision_check", {}).get("status") != "PASS":
        raise ValueError("Preview requires a passed final-position collision check")
    check = report["insertion_check"]
    status = check["status"]
    if status not in {"PASS", "BLOCKED"}:
        raise ValueError("Unsupported insertion status")
    instances = report["instances"]
    if not instances or len(instances) != report["module_count"]:
        raise ValueError("Inconsistent module count")
    names = [item["name"] for item in instances]
    if any(not isinstance(name, str) for name in names) or len(set(names)) != len(
        names
    ):
        raise ValueError("Module names must be unique strings")
    order = check["assembly_order"]
    if status == "PASS" and (len(order) != len(names) or set(order) != set(names)):
        raise ValueError(
            "Passed insertion order must contain every module exactly once"
        )
    if status == "BLOCKED" and order:
        raise ValueError("Blocked report cannot contain a complete assembly order")
    pitch = report["pitch_mm"]
    values = [pitch]
    for item in instances:
        position = item["position_mm"]
        if len(position) != 3:
            raise ValueError("Expected XYZ positions")
        values.extend(position)
    if (
        any(
            isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v)
            for v in values
        )
        or pitch <= 0
    ):
        raise ValueError("Preview dimensions must be finite with positive pitch")
    if len({i["position_mm"][2] for i in instances}) != 1:
        raise ValueError("Top-view preview requires a single module level")
    xs = [i["position_mm"][0] for i in instances]
    ys = [i["position_mm"][1] for i in instances]
    scale = 100 / pitch
    width = max(660, (max(xs) - min(xs)) * scale + 220)
    height = (max(ys) - min(ys)) * scale + 320
    svg = Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        viewBox=f"0 0 {width:g} {height:g}",
        role="img",
    )
    SubElement(svg, "title").text = "Garden assembly — numbered top view"
    SubElement(svg, "desc").text = (
        "Module centers and insertion steps from the checked report. "
        "Schematic square footprints omit projecting connectors."
    )
    SubElement(svg, "rect", width="100%", height="100%", fill="#f5f7f5")

    def text(x, y, value, size=16, **attributes):
        SubElement(
            svg,
            "text",
            x=str(x),
            y=str(y),
            fill="#183329",
            **{"font-family": "sans-serif", "font-size": str(size), **attributes},
        ).text = value

    text(30, 38, "GARDEN / ASSEMBLY ORDER", 23)
    text(30, 68, f"{len(names)} modules · {pitch:g} mm pitch · insertion {status}")
    text(30, 94, "Top view: +X right, +Y up. Lower each module from +Z.")
    steps = {name: index + 1 for index, name in enumerate(order)}
    for item in instances:
        x, y, z = item["position_mm"]
        cx = 110 + (x - min(xs)) * scale
        cy = 180 + (max(ys) - y) * scale
        group = SubElement(
            svg,
            "g",
            {
                "data-module": item["name"],
                "data-step": str(steps.get(item["name"], "")),
            },
        )
        SubElement(group, "title").text = f"{item['name']}: ({x:g}, {y:g}, {z:g}) mm"
        SubElement(
            group,
            "rect",
            x=str(cx - 46),
            y=str(cy - 46),
            width="92",
            height="92",
            rx="7",
            fill="#dceee3" if status == "PASS" else "#ffe1ca",
            stroke="#426b54",
            **{"stroke-width": "2"},
        )
        text(
            cx,
            cy + 3,
            str(steps[item["name"]]) if status == "PASS" else "—",
            28,
            **{"text-anchor": "middle"},
        )
        text(
            cx,
            cy + 27,
            f"r{item['row']} c{item['column']}",
            12,
            **{"text-anchor": "middle"},
        )
    text(
        30,
        height - 55,
        "Numbers = checked insertion steps."
        if status == "PASS"
        else "BLOCKED — no complete insertion order. See report.json for blockers.",
    )
    text(
        30,
        height - 31,
        "Schematic: connectors omitted. Nominal geometry; physical fit unverified.",
        14,
    )
    return tostring(svg, encoding="unicode") + "\n"
