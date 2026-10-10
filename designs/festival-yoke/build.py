"""Parametric festival yoke: sloped shoulder collar with a module rail and an LED lip.
Run: uv run --no-project --with cadquery build.py"""
import math
import tomllib
from pathlib import Path

import cadquery as cq

import sizing

ROOT = Path(__file__).parent
cfg = tomllib.loads((ROOT / "config.toml").read_text())
SIZE, W = sizing.resolve(cfg)
OUT = ROOT / "out" / SIZE
Y, R, G, P, J = cfg["yoke"], cfg["rail"], cfg["glow"], cfg["print"], cfg["joint"]
PAD, D = cfg["pad"], cfg["diffuser"]

AI, BI = W["neck_opening_a"], W["neck_opening_b"]
AO, BO = W["shoulder_half_width"], W["shoulder_half_depth"]
DROP = W["shoulder_drop"]


def surface(u: float) -> tuple[float, float, float]:
    """Ellipse on the collar surface; u=0 neck edge, u=1 outer edge. Returns (a, b, z)."""
    return AI + (AO - AI) * u, BI + (BO - BI) * u, -DROP * u


def ring(u: float, inner: float, outer: float, z0: float, h: float) -> cq.Workplane:
    """Elliptical wall centred on surface(u), extending `inner`/`outer` mm either side, from z0 up h."""
    a, b, _ = surface(u)
    big = cq.Workplane("XY").workplane(offset=z0).ellipse(a + outer, b + outer).extrude(h)
    small = cq.Workplane("XY").workplane(offset=z0 - 1).ellipse(a - inner, b - inner).extrude(h + 2)
    return big.cut(small)


def cone(dz: float) -> cq.Workplane:
    """Solid frustum under the collar surface, shifted down by dz."""
    return (
        cq.Workplane("XY").workplane(offset=dz).ellipse(AI, BI)
        .workplane(offset=-DROP).ellipse(AO, BO).loft()
    )


def skin() -> cq.Workplane:
    """Collar skin with rounded edges. Rounding is attempted at decreasing radii until the finished skin is a valid
    solid (the kernel is fragile on some sizes); with none valid it is left sharp and a warning is printed."""
    for r in (Y["round"], Y["round"] * 0.8, Y["round"] * 0.6, Y["round"] * 0.4):
        s = _skin(r)
        if s.val().isValid() and s.val().Volume() > 0:
            return s
    print("WARN edge rounding skipped for this size (kernel could not produce a valid rounded skin)")
    return _skin(0)


def _skin(r: float) -> cq.Workplane:
    t = Y["thickness"]
    s = cone(0).cut(cone(-t))
    k = (AO - AI) * t / DROP + 1
    s = s.cut(cq.Workplane("XY").workplane(offset=-DROP - 5).ellipse(AI + k, BI + k).extrude(DROP + 10))
    if r:
        s = s.edges().fillet(r)  # round the neck and shoulder edges before anything else is cut into it
    # lightening slots, skipping the front gap (60-120 deg)
    length = (AO - AI) * 0.38
    for deg in range(15, 360, 30):  # offset so no slot sits on a seam
        if 60 <= deg <= 120:
            continue
        th = math.radians(deg)
        a, b, _ = surface(0.45)
        slot = (
            cq.Workplane("XY").workplane(offset=-DROP - 5).center(math.cos(th) * a, math.sin(th) * b)
            .slot2D(length, Y["slot_width"], deg).extrude(DROP + 10)
        )
        s = s.cut(slot)
    return s


def rail() -> cq.Workplane:
    u = R["position"]
    z = surface(u)[2] - 2  # sink 2 mm into the skin
    stem = ring(u, R["stem_width"] / 2, R["stem_width"] / 2, z, R["stem_height"] + 2)
    cap = ring(u, R["cap_width"] / 2, R["cap_width"] / 2, z + R["stem_height"] + 2, R["cap_height"])
    return stem.union(cap)


LIP_SETBACK = 0.6


def lip() -> cq.Workplane:
    w = G["lip_width"]
    return ring(1.0, w + LIP_SETBACK, -LIP_SETBACK, -DROP - 1, G["lip_height"] + 1)  # set back from the rim so it never shares a surface with the rounded edge


def pads() -> cq.Workplane:
    """Skin-conforming seats under the collar for stick-on foam."""
    t = Y["thickness"]
    band = cone(-t + 0.3).cut(cone(-t - PAD["thickness"]))  # overlaps the skin by 0.3 mm so the union is clean
    a, b, _ = surface(PAD["position"])
    out = None
    for deg in PAD["angles"]:
        th = math.radians(deg)
        cx, cy = a * math.cos(th), b * math.sin(th)
        heading = math.degrees(math.atan2(a * math.sin(th), b * math.cos(th)))
        oval = (
            cq.Workplane("XY").workplane(offset=-DROP - 8).center(cx, cy)
            .ellipse(PAD["length"] / 2, PAD["width"] / 2).extrude(DROP + 16)
            .rotate((cx, cy, 0), (cx, cy, 1), heading)
        )
        piece = band.intersect(oval)
        out = piece if out is None else out.union(piece)
    return out


def diffuser() -> cq.Workplane:
    """Thin cover over the LED channel between rail and lip. Outer hook grips the lip."""
    t, gp = D["thickness"], D["gap"]
    a0, b0, zs = surface(R["position"])
    rail_top = zs + R["stem_height"] + R["cap_height"]
    lip_top = -DROP + G["lip_height"]
    zA, zB = rail_top + gp + t, lip_top + gp + t
    aA, bA = a0 + R["cap_width"] / 2, b0 + R["cap_width"] / 2
    aB, bB = AO + 1.4, BO + 1.4
    dz = zA - zB
    ka, kb = (aB - aA) * t / dz + 0.5, (bB - bA) * t / dz + 0.5

    def frustum(shift):
        return (
            cq.Workplane("XY").workplane(offset=zA + shift).ellipse(aA - ka, bA - kb)
            .workplane(offset=-dz).ellipse(aB, bB).loft()
        )

    band = frustum(0).cut(frustum(-t))
    band = band.cut(cq.Workplane("XY").workplane(offset=zB - 5).ellipse(aA, bA).extrude(dz + 10))
    hook = ring(1.0, LIP_SETBACK - 0.1, 1.4, zB - t - D["hook"], D["hook"] + t)
    # small flange on the inner edge locates the cover against the rail cap
    flange = ring(R["position"], -(R["cap_width"] / 2 + 0.2), R["cap_width"] / 2 + 1.4, zA - t - 2.5, 2.5 + t)
    return band.union(hook).union(flange).cut(gap())


def gap() -> cq.Workplane:
    return cq.Workplane("XY").box(Y["front_gap"], BO * 3, DROP * 4).translate((0, BO, 0))


def components() -> dict[str, cq.Workplane]:
    g = gap()
    return {"skin": skin().cut(g), "rail": rail().cut(g), "lip": lip().cut(g), "pad": pads()}


def yoke() -> cq.Workplane:
    c = components()
    return c["skin"].union(c["rail"]).union(c["lip"]).union(c["pad"])


QUARTERS = {"fr": (1, 1), "br": (1, -1), "fl": (-1, 1), "bl": (-1, -1)}


def quarter(shape: cq.Workplane, sx: int, sy: int) -> cq.Workplane:
    big = 2000
    return shape.intersect(cq.Workplane("XY").box(big, big, big).translate((sx * big / 2, sy * big / 2, 0)))


def dovetail(c: float = 0.0) -> list[tuple[float, float]]:
    """Dovetail tab in seam coordinates (s along the seam, d across it into the receiving part)."""
    r, t, n = J["root_width"] / 2 + c, J["tip_width"] / 2 + c, J["length"] + c
    return [(-r, -3), (r, -3), (r, 0), (t, n), (-t, n), (-r, 0)]


def prism(pts: list[tuple[float, float]]) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=-DROP - 6).polyline(pts).close().extrude(DROP + 12)


def parts() -> dict[str, cq.Workplane]:
    """The four print quarters with dovetail joints: each seam has tabs on one part, matching pockets on the other."""
    y = yoke()
    q = {name: quarter(y, sx, sy) for name, (sx, sy) in QUARTERS.items()}

    # (tab part, pocket part, seam point at u -> (x, y), local (s, d) -> global (x, y))
    seams = [
        ("fr", "br", J["positions_side"], lambda u: (surface(u)[0], 0), lambda p, s, d: (p[0] + s, -d)),
        ("fl", "bl", J["positions_side"], lambda u: (-surface(u)[0], 0), lambda p, s, d: (p[0] - s, -d)),
        ("br", "bl", J["positions_back"], lambda u: (0, -surface(u)[1]), lambda p, s, d: (-d, p[1] + s)),
    ]
    for tab_part, pocket_part, us, at, to_global in seams:
        for u in us:
            p = at(u)
            tab = [to_global(p, s, d) for s, d in dovetail()]
            pocket = [to_global(p, s, d) for s, d in dovetail(J["clearance"])]
            q[tab_part] = q[tab_part].union(y.intersect(prism(tab)))
            q[pocket_part] = q[pocket_part].cut(prism(pocket))
    return q


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    y = yoke()
    q = parts()
    bed, total = P["bed"], 0.0
    print(f"size {SIZE}")
    for line in sizing.fit_report(W, Y["front_gap"]):
        print("  " + line)
    print(f"{'part':<10}{'bbox mm (x y z)':<24}{'solid g':>9}  fits bed")
    for name, shp in q.items():
        bb = shp.val().BoundingBox()
        dims = sorted([bb.xlen, bb.ylen])
        fits = dims[0] <= min(bed[:2]) and dims[1] <= max(bed[:2]) and bb.zlen <= bed[2]
        g = shp.val().Volume() / 1000 * P["density_g_cc"]
        total += g
        cq.exporters.export(shp, str(OUT / f"yoke_{name}.stl"))
        print(f"yoke_{name:<5}{bb.xlen:6.0f}{bb.ylen:6.0f}{bb.zlen:6.0f}      {g:>9.1f}  {'ok' if fits else 'TOO BIG'}")
    cq.exporters.export(y, str(OUT / "assembly.stl"))

    # LED diffuser cover, printed in the same four quarters
    dif = diffuser()
    dtotal = 0.0
    for name, (sx, sy) in QUARTERS.items():
        dq = quarter(dif, sx, sy)
        bb = dq.val().BoundingBox()
        dims = sorted([bb.xlen, bb.ylen])
        fits = dims[0] <= min(bed[:2]) and dims[1] <= max(bed[:2]) and bb.zlen <= bed[2]
        g = dq.val().Volume() / 1000 * P["density_g_cc"]
        dtotal += g
        total += g
        cq.exporters.export(dq, str(OUT / f"diffuser_{name}.stl"))
        print(f"diffuser_{name:<2}{bb.xlen:6.0f}{bb.ylen:6.0f}{bb.zlen:6.0f}      {g:>9.1f}  {'ok' if fits else 'TOO BIG'}")
    touch = dif.intersect(y)
    touch_mm3 = sum(s.Volume() for s in touch.solids().vals()) if touch.vals() else 0.0

    # joint check: tabs must not overlap their pockets, and the glued-up whole should match the unsplit yoke
    overlap = sum(q[a].intersect(q[b]).val().Volume() for a, b in (("fr", "br"), ("fl", "bl"), ("br", "bl")) if q[a].intersect(q[b]).vals())
    missing = y.val().Volume() - sum(s.val().Volume() for s in q.values())
    loose = [n for n, s in q.items() if len(s.solids().vals()) != 1]
    need = max(max(s.val().BoundingBox().xlen, s.val().BoundingBox().ylen) for s in list(q.values()) + [quarter(dif, sx, sy) for sx, sy in QUARTERS.values()])
    print(f"\nSmallest square bed that fits every part: {need:.0f} mm (configured {min(bed[:2])} mm)")
    print(f"Total solid-plastic upper bound: {total:.0f} g (skin is thin, real print is lighter)")
    print(f"Joint check: part-to-part overlap {overlap:.2f} mm3 (want 0), clearance gaps {missing:.0f} mm3, loose crumbs: {loose or "none"}")
    a0, b0, _ = surface(R["position"])
    channel = min((AO - G["lip_width"]) - (a0 + R["cap_width"] / 2), (BO - G["lip_width"]) - (b0 + R["cap_width"] / 2))
    print(f"LED channel between rail and lip: {channel:.1f} mm wide at its narrowest (fits an 8 mm strip: {'yes' if channel >= 8 else 'NO'})")
    print(f"Diffuser: {dtotal:.0f} g of the total, overlap with yoke {touch_mm3:.2f} mm3 (want 0)")
    print(f"Highest point: {y.val().BoundingBox().zmax:.1f} mm vs neck edge. Nothing above the shoulders.")


if __name__ == "__main__":
    main()
