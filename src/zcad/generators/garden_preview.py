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
    positions = {i["name"]: i["position_mm"] for i in instances}
    expected = set()
    for male, a in positions.items():
        for female, b in positions.items():
            for axis, delta in (("X", (pitch, 0)), ("Y", (0, pitch))):
                if male != female and all(
                    math.isclose(b[k] - a[k], delta[k], abs_tol=1e-8, rel_tol=1e-9)
                    for k in (0, 1)
                ):
                    expected.add((male, female, axis))
    connections = report["connections"]
    actual = {(c["male"], c["female"], c["axis"]) for c in connections}
    if (
        actual != expected
        or len(actual) != len(connections)
        or len(actual) != report["connection_count"]
    ):
        raise ValueError("Connections do not match neighboring module positions")
    mates = {}
    for male, female, axis in actual:
        mates[male, "+" + axis] = female
        mates[female, "-" + axis] = male
    scale = 140 / pitch
    width = max(760, (max(xs) - min(xs)) * scale + 220)
    height = (max(ys) - min(ys)) * scale + 410
    svg = Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        viewBox=f"0 0 {width:g} {height:g}",
        role="img",
    )
    SubElement(svg, "title").text = "Garden assembly — numbered top view"
    SubElement(svg, "desc").text = (
        "Module centers and insertion steps from the checked report. "
        "Male rails are filled blue; female slots are open purple. "
        "Green links identify checked mates; dashed amber edges are exposed."
    )
    SubElement(svg, "rect", width="100%", height="100%", fill="#f5f7f5")

    def text(x, y, value, size=16, parent=None, **attributes):
        SubElement(
            svg if parent is None else parent,
            "text",
            x=str(x),
            y=str(y),
            fill="#183329",
            **{"font-family": "sans-serif", "font-size": str(size), **attributes},
        ).text = value

    text(30, 38, "GARDEN / ASSEMBLY ORDER", 23)
    text(30, 68, f"{len(names)} modules · {pitch:g} mm pitch · insertion {status}")
    text(30, 94, "Top view: +X right, +Y up. Lower each module from +Z.")
    centers = {
        name: (110 + (p[0] - min(xs)) * scale, 180 + (max(ys) - p[1]) * scale)
        for name, p in positions.items()
    }
    for male, female, axis in sorted(actual):
        a, b = centers[male], centers[female]
        SubElement(
            svg,
            "line",
            x1=str(a[0]),
            y1=str(a[1]),
            x2=str(b[0]),
            y2=str(b[1]),
            stroke="#24734b",
            **{
                "stroke-width": "3",
                "data-connection": axis,
                "data-male": male,
                "data-female": female,
            },
        )
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
        for side, angle, kind in (
            ("+X", 0, "male"),
            ("+Y", -90, "male"),
            ("-X", 180, "female"),
            ("-Y", 90, "female"),
        ):
            mate = mates.get((item["name"], side))
            connector = SubElement(
                group,
                "g",
                {
                    "data-side": side,
                    "data-kind": kind,
                    "data-state": "connected" if mate else "exposed",
                    "data-mate": mate or "",
                    "transform": f"translate({cx},{cy}) rotate({angle})",
                },
            )
            SubElement(connector, "title").text = (
                f"{side} {kind}: mates with {mate}"
                if mate
                else f"{side} {kind}: exposed"
            )
            if not mate:
                SubElement(
                    connector,
                    "line",
                    x1="46",
                    x2="46",
                    y1="-37",
                    y2="37",
                    stroke="#a85b13",
                    **{"stroke-width": "3", "stroke-dasharray": "5 4"},
                )
            SubElement(
                connector,
                "polygon",
                points="46,-6 57,-11 57,11 46,6"
                if kind == "male"
                else "46,-6 35,-11 35,11 46,6",
                fill="#246ba0" if kind == "male" else "#f5f7f5",
                stroke="#246ba0" if kind == "male" else "#7945a0",
                **{"stroke-width": "2"},
            )
        text(
            cx,
            cy + 3,
            str(steps[item["name"]]) if status == "PASS" else "—",
            28,
            parent=group,
            **{"text-anchor": "middle"},
        )
        text(
            cx,
            cy + 27,
            f"r{item['row']} c{item['column']}",
            12,
            parent=group,
            **{"text-anchor": "middle"},
        )
    text(
        30,
        height - 145,
        "Numbers = checked insertion steps."
        if status == "PASS"
        else "BLOCKED — no complete insertion order. See report.json for blockers.",
    )
    text(
        30,
        height - 31,
        "Schematic symbols, not connector dimensions. Physical fit unverified.",
        14,
    )
    text(
        30,
        height - 115,
        "Filled blue = male rail (+X, +Y). Open purple = female slot (−X, −Y).",
        14,
    )
    text(
        30,
        height - 89,
        "Green links = checked mates. Dashed amber edges = exposed connectors.",
        14,
    )
    text(
        30,
        height - 63,
        f"{len(actual)} connected pairs · "
        f"{4 * len(names) - 2 * len(actual)} exposed edges",
        14,
    )
    return tostring(svg, encoding="unicode") + "\n"
