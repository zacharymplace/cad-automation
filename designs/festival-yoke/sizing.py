"""Turn a handful of body measurements into the yoke's dimensions.

Pick a preset with `size = "M"` in config.toml or FESTIVAL_YOKE_SIZE=L in the environment;
`size = "custom"` uses the [custom] table. See MEASURING.md.
"""
import math
import os

HEAD_EASE = 14.0   # mm each side between head width and the yoke opening
HEAD_RATIO = 0.8   # head width : head length, a typical adult ratio


def head_axes(circumference: float) -> tuple[float, float]:
    """Semi-axes (half width, half length) of an elliptical head of this circumference."""
    p = HEAD_RATIO
    k = math.pi * (3 * (p + 1) - math.sqrt((3 * p + 1) * (p + 3)))
    q = circumference / k
    return p * q, q


def resolve(cfg: dict) -> tuple[str, dict]:
    size = os.environ.get("FESTIVAL_YOKE_SIZE") or cfg["size"]
    table = cfg["custom"] if size == "custom" else cfg["sizes"][size]
    p, q = head_axes(table["head_circumference"])
    return size, {
        "head_circumference": table["head_circumference"],
        "neck_circumference": table["neck_circumference"],
        "neck_opening_a": round(p + HEAD_EASE, 1),
        "neck_opening_b": round(0.85 * q, 1),
        "shoulder_half_width": table["shoulder_width"] / 2,
        "shoulder_half_depth": table["shoulder_depth"] / 2,
        "shoulder_drop": table["shoulder_drop"],
    }


def fit_report(W: dict, front_gap: float) -> list[str]:
    """Plain-language checks on the resolved dimensions. Lines starting 'WARN' need attention."""
    p, q = head_axes(W["head_circumference"])
    neck_r = W["neck_circumference"] / (2 * math.pi)
    ai, bi = W["neck_opening_a"], W["neck_opening_b"]
    ao, bo = W["shoulder_half_width"], W["shoulder_half_depth"]
    out = [
        f"head ~{2 * p:.0f} wide x {2 * q:.0f} long; opening {2 * ai:.0f} wide x {2 * bi:.0f} deep, front gap {front_gap:.0f}",
        f"opening is {ai - neck_r:.0f} mm (sides) / {bi - neck_r:.0f} mm (front-back) clear of the neck",
    ]
    if 2 * bi < 2 * q:
        out.append(f"head is {2 * q - 2 * bi:.0f} mm longer than the opening is deep: it has to tilt through the front gap (untested on a body)")
    if ai - neck_r > 55:
        out.append("WARN opening is loose round the neck, the yoke may slide: use a smaller size or pads")
    if ai - neck_r < 15:
        out.append("WARN opening is tight round the neck")
    if ao - ai < 75:
        out.append("WARN shoulders are narrow for this head: not enough collar for the rail and joints")
    if bo - bi < 30:
        out.append("WARN collar is shallow front to back")
    return out
