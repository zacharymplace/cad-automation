"""Flat-print patterns for the collar skin.

The collar is (almost exactly) a developable cone, so each quarter can be printed flat in TPU with no supports and
then bent into the cone on assembly. This module unrolls each quarter with a least-squares conformal map, checks
the stretch, and builds the flat TPU pieces: outline, slots, dovetail tabs and pockets, and engraved guide lines for
the rail, the lip and the foam seats. The rail and lip are separate rigid segments (see `hoop_segments`).

Run: uv run --no-project --with cadquery flatpack.py
"""
import math

import cadquery as cq
import numpy as np
import scipy.sparse as sp
from scipy.interpolate import LinearNDInterpolator
from scipy.sparse.linalg import spsolve

import build

AI, BI, AO, BO, DROP = build.AI, build.BI, build.AO, build.BO, build.DROP
T = build.Y["thickness"]
K = (AO - AI) * T / DROP + 1                   # hole is cut this much bigger than the neck ellipse (see build._skin)
GROOVE_W, GROOVE_D = 0.8, 0.4                  # engraved guide lines
N_S, N_T = 24, 48                              # grid resolution across and along the quarter


def z_of(x: float, y: float) -> float:
    """Height of the collar surface above the plan point (x, y)."""
    lo, hi = 0.0, 1.0
    for _ in range(40):
        u = (lo + hi) / 2
        a, b = AI + (AO - AI) * u, BI + (BO - BI) * u
        if (x / a) ** 2 + (y / b) ** 2 > 1:
            lo = u
        else:
            hi = u
    return -DROP * (lo + hi) / 2


def coons(xcut: float):
    """Plan-view grid (x, y >= 0) of one quarter: Coons patch between the seam, the hole, the rim and the cut at x = xcut."""
    ah, bh = AI + K, BI + K
    xh0 = ah
    yh = bh * math.sqrt(max(0.0, 1 - (xcut / ah) ** 2))
    yo = BO * math.sqrt(max(0.0, 1 - (xcut / AO) ** 2))
    ph, po = math.acos(xcut / ah), math.acos(xcut / AO)
    c00, c10, c01, c11 = np.array([xh0, 0]), np.array([AO, 0]), np.array([xcut, yh]), np.array([xcut, yo])
    B = lambda s: c00 + (c10 - c00) * s
    Tp = lambda s: c01 + (c11 - c01) * s
    L = lambda t: np.array([ah * math.cos(ph * t), bh * math.sin(ph * t)])
    R = lambda t: np.array([AO * math.cos(po * t), BO * math.sin(po * t)])
    pts = np.zeros((N_T + 1, N_S + 1, 2))
    for j in range(N_T + 1):
        t = j / N_T
        for i in range(N_S + 1):
            s = i / N_S
            pts[j, i] = ((1 - t) * B(s) + t * Tp(s) + (1 - s) * L(t) + s * R(t)
                         - ((1 - s) * (1 - t) * c00 + s * (1 - t) * c10 + (1 - s) * t * c01 + s * t * c11))
    return pts


def lscm(V: np.ndarray, tris: np.ndarray, pin: tuple[int, int]):
    """Least-squares conformal map of a triangle mesh to the plane, pinned so the edge pin[0]-pin[1] lies on the x axis."""
    n = len(V)
    rows, cols, vals = [], [], []
    r = 0
    for tri in tris:
        p = V[tri]
        e1, e2 = p[1] - p[0], p[2] - p[0]
        x1 = np.linalg.norm(e1)
        ex = e1 / x1
        nrm = np.cross(e1, e2)
        A2 = np.linalg.norm(nrm)
        ey = np.cross(nrm / A2, ex)
        z = np.array([0j, complex(x1, 0), complex(e2 @ ex, e2 @ ey)])
        d = np.array([z[2] - z[1], z[0] - z[2], z[1] - z[0]])
        w = 1.0 / math.sqrt(A2)
        for j in range(3):
            a, b = d[j].real * w, d[j].imag * w
            rows += [r, r, r + 1, r + 1]
            cols += [tri[j], n + tri[j], tri[j], n + tri[j]]
            vals += [a, -b, b, a]
        r += 2
    M = sp.csr_matrix((vals, (rows, cols)), shape=(r, 2 * n))
    i0, i1 = pin
    L = float(np.linalg.norm(V[i1] - V[i0]))
    fixed = {i0: 0.0, n + i0: 0.0, i1: L, n + i1: 0.0}
    free = np.array([q for q in range(2 * n) if q not in fixed])
    rhs = -M[:, list(fixed)] @ np.array(list(fixed.values()))
    A = M[:, free]
    U = np.zeros(2 * n)
    U[free] = spsolve((A.T @ A).tocsc(), A.T @ rhs)
    for q, v in fixed.items():
        U[q] = v
    return np.stack([U[:n], U[n:]], axis=1)


class Pattern:
    """One flattened quarter: plan grid, flat coordinates, boundary loop and a plan-to-flat map."""

    def __init__(self, sx: int, sy: int, xcut: float):
        g = coons(xcut)
        self.sx, self.sy, self.xcut = sx, sy, xcut
        V = np.array([[sx * p[0], sy * p[1], z_of(p[0], p[1])] for row in g for p in row])
        self.plan = V[:, :2]
        idx = lambda j, i: j * (N_S + 1) + i
        tris = []
        for j in range(N_T):
            for i in range(N_S):
                a, b, c, d = idx(j, i), idx(j + 1, i), idx(j + 1, i + 1), idx(j, i + 1)
                tris += [(a, b, c), (a, c, d)]
        self.V, self.tris = V, np.array(tris)
        uv = lscm(V, self.tris, (idx(0, 0), idx(0, N_S)))
        # keep the outside (+z) face up: flat triangles must wind the same way as their 3D normals seen from above
        a, b, c = self.tris[0]
        n3 = np.cross(V[b] - V[a], V[c] - V[a])[2]
        n2 = (uv[b][0] - uv[a][0]) * (uv[c][1] - uv[a][1]) - (uv[c][0] - uv[a][0]) * (uv[b][1] - uv[a][1])
        if n3 * n2 < 0:
            uv[:, 0] *= -1
        uv -= uv.min(axis=0)
        self.uv = uv
        self.idx = idx
        self.map = LinearNDInterpolator(self.plan, uv)
        self.stretch = self._stretch()

    def _stretch(self):
        edges = {tuple(sorted(e)) for t in self.tris for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0]))}
        r = np.array([np.linalg.norm(self.uv[a] - self.uv[b]) / np.linalg.norm(self.V[a] - self.V[b]) for a, b in edges])
        return float(r.min()), float(r.max())

    def outline(self) -> np.ndarray:
        """Boundary loop: seam edge, rim, cut edge (back to the hole), hole."""
        i = self.idx
        loop = [i(0, s) for s in range(N_S + 1)]                       # seam, hole to rim
        loop += [i(j, N_S) for j in range(1, N_T + 1)]                  # rim, seam end to cut end
        loop += [i(N_T, s) for s in range(N_S - 1, -1, -1)]             # cut edge, rim to hole
        loop += [i(j, 0) for j in range(N_T - 1, 0, -1)]                # hole, back to the seam
        return self.uv[loop]

    def to_flat(self, plan_pts: np.ndarray) -> np.ndarray:
        """Map plan-view points (in this quarter's own signs) to flat coordinates; NaN outside the quarter."""
        return self.map(plan_pts)

    def edge_frame(self, which: str):
        """Seam edge 'seam' (y = 0) or 'cut' (x = xcut) as (start, end, outward normal, length) in flat coordinates, start at the hole."""
        i = self.idx
        a, b = (i(0, 0), i(0, N_S)) if which == "seam" else (i(N_T, 0), i(N_T, N_S))
        p, q = self.uv[a], self.uv[b]
        t = (q - p) / np.linalg.norm(q - p)
        centre = self.uv.mean(axis=0)
        n = np.array([-t[1], t[0]])
        if (centre - p) @ n > 0:
            n = -n
        return p, q, n, float(np.linalg.norm(q - p))


def strip_polygon(poly: np.ndarray, width: float, closed: bool = False) -> np.ndarray:
    """Outline polygon of a polyline thickened to `width` (miter-free, for gentle curves)."""
    d = np.gradient(poly, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-12
    nrm = np.stack([-d[:, 1], d[:, 0]], axis=1) * width / 2
    return np.vstack([poly + nrm, (poly - nrm)[::-1]])


def prism(poly: np.ndarray, z0: float, h: float) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=z0).polyline([tuple(p) for p in poly]).close().extrude(h)


def slot_plan(theta_deg: float):
    """Plan-view outline of one lightening slot (same placement as build._skin)."""
    a, b, _ = build.surface(0.42)
    th = math.radians(theta_deg)
    cx, cy = math.cos(th) * a, math.sin(th) * b
    length, width = (AO - AI) * 0.30, build.Y["slot_width"]
    r = width / 2
    half = max(length - width, 0) / 2
    ang = math.radians(theta_deg)
    pts = []
    for k in range(13):                      # semicircle at +end
        t = -math.pi / 2 + math.pi * k / 12
        pts.append((half + r * math.cos(t), r * math.sin(t)))
    for k in range(13):                      # semicircle at -end
        t = math.pi / 2 + math.pi * k / 12
        pts.append((-half + r * math.cos(t), r * math.sin(t)))
    c, s = math.cos(ang), math.sin(ang)
    return np.array([(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts])


def ellipse_arc(u: float, th0: float, th1: float, n: int = 80) -> np.ndarray:
    a, b, _ = build.surface(u)
    th = np.linspace(th0, th1, n)
    return np.stack([a * np.cos(th), b * np.sin(th)], axis=1)


def dovetail_pts(c: float = 0.0):
    r, t, n = build.J["root_width"] / 2 + c, build.J["tip_width"] / 2 + c, build.J["length"] + c
    return [(-r, -3), (r, -3), (r, 0), (t, n), (-t, n), (-r, 0)]


def piece(name: str, sx: int, sy: int, xcut: float, tab_edges: list[str], pocket_edges: list[str]):
    """Build one flat TPU piece. tab_edges / pocket_edges name the edges ('seam' or 'cut') that carry tabs or pockets."""
    pat = Pattern(sx, sy, xcut)
    outline = pat.outline()
    body = prism(outline, 0, T)

    def on_edge(which, u, poly, outward_sign):
        p, q, n, length = pat.edge_frame(which)
        if which == "seam":
            hole0, rim = AI + K, AO
            pos = (build.surface(u)[0] - hole0) / (rim - hole0)
        else:
            ah, bh = AI + K, BI + K
            yh = bh * math.sqrt(max(0.0, 1 - (xcut / ah) ** 2))
            yo = BO * math.sqrt(max(0.0, 1 - (xcut / AO) ** 2))
            pos = (build.surface(u)[1] - yh) / (yo - yh)
        base = p + (q - p) * pos
        t = (q - p) / length
        return np.array([base + t * s + n * d * outward_sign for s, d in poly])

    for which in tab_edges:
        us = build.J["positions_side"] if which == "seam" else build.J["positions_back"]
        for u in us:
            body = body.union(prism(on_edge(which, u, dovetail_pts(), 1), 0, T))
    for which in pocket_edges:
        us = build.J["positions_side"] if which == "seam" else build.J["positions_back"]
        for u in us:
            body = body.cut(prism(on_edge(which, u, dovetail_pts(build.J["clearance"]), -1), -1, T + 2))

    # lightening slots, same angles as the formed skin; keep those inside this quarter
    for deg in range(15, 360, 30):
        if 60 <= deg <= 120:
            continue
        pts = slot_plan(deg)
        # the slot belongs to this quarter if its centre lies in it; its outline is mapped through this quarter's grid
        a, b, _ = build.surface(0.42)
        ctr = np.array([math.cos(math.radians(deg)) * a, math.sin(math.radians(deg)) * b])
        if (np.sign(ctr[0]) != sx) or (np.sign(ctr[1]) != sy):
            continue
        flat = pat.to_flat(pts)          # slot_plan already carries the real plan signs
        if np.isnan(flat).any():
            continue
        body = body.cut(prism(flat, -1, T + 2))

    # engraved guide lines on the top face: rail and lip centre lines, and the foam seat ovals
    def engrave(poly_plan, closed=False):
        nonlocal body
        f = pat.to_flat(poly_plan * np.array([sx, sy]))
        f = f[~np.isnan(f).any(axis=1)]
        if len(f) < 3:
            return
        body = body.cut(prism(strip_polygon(f, GROOVE_W), T - GROOVE_D, GROOVE_D + 1))

    ph0 = 0.02
    for u in (build.R["position"], build.LIP_U):
        th_end = math.acos(min(0.999, xcut / build.surface(u)[0]))
        engrave(ellipse_arc(u, ph0, th_end - 0.02))
    for deg in build.PAD["angles"]:
        th = math.radians(deg)
        if (math.cos(th) > 0) != (sx > 0) or (math.sin(th) > 0) != (sy > 0):
            continue
        a, b, _ = build.surface(build.PAD["position"])
        cx, cy = abs(a * math.cos(th)), abs(b * math.sin(th))
        ang = math.atan2(abs(a * math.sin(th)), abs(b * math.cos(th)))
        t = np.linspace(0, 2 * math.pi, 48)
        ox, oy = build.PAD["length"] / 2 * np.cos(t), build.PAD["width"] / 2 * np.sin(t)
        pts = np.stack([cx + ox * math.cos(ang) - oy * math.sin(ang), cy + ox * math.sin(ang) + oy * math.cos(ang)], axis=1)
        engrave(pts)
    return pat, body


# the four quarters: (name, sx, sy, xcut, tab edges, pocket edges)
SPECS = {
    "fr": (1, 1, build.Y["front_gap"] / 2, ["seam"], []),
    "br": (1, -1, 0.0, ["cut"], ["seam"]),
    "fl": (-1, 1, build.Y["front_gap"] / 2, ["seam"], []),
    "bl": (-1, -1, 0.0, [], ["seam", "cut"]),
}


def flat_parts():
    """name -> (Pattern, solid) for the four flat skin quarters."""
    out = {}
    for name, (sx, sy, xcut, tabs, pockets) in SPECS.items():
        out[name] = piece(name, sx, sy, xcut, tabs, pockets)
    return out


SEGMENTS = {          # sector of the ring each rigid segment covers, degrees (0 = right side, 90 = front); cuts fall away from the skin seams
    "right": (-45, 45), "front_right": (45, 90), "front_left": (90, 135), "left": (135, 225), "back": (225, 315),
}


def _sector(a0: float, a1: float) -> cq.Workplane:
    pts = [(0, 0)] + [(600 * math.cos(math.radians(a)), 600 * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 12)]
    return cq.Workplane("XY").workplane(offset=-200).polyline(pts).close().extrude(400)


def hoop_segments() -> dict[str, cq.Workplane]:
    """Rigid rail and lip segments, base cut to the skin surface so they sit flat on it; print them upside down (cap or
    lip top on the bed) and they need no supports. Segments straddle the skin seams, which stiffens the joints."""
    R, G = build.R, build.G
    zs = build.surface(R["position"])[2]
    stem = build.ring(R["position"], R["stem_width"] / 2, R["stem_width"] / 2, zs - 8, 8 + R["stem_height"])
    cap = build.ring(R["position"], R["cap_width"] / 2, R["cap_width"] / 2, zs + R["stem_height"], R["cap_height"])
    rail = stem.union(cap).cut(build.cone(0))
    zl = build.surface(build.LIP_U)[2]
    lip = build.ring(build.LIP_U, G["lip_width"] / 2, G["lip_width"] / 2, zl - 8, 8 + G["lip_height"])
    lip = lip.cut(build.ring(build.LIP_U, 0.5 - G["lip_width"] / 2, G["lip_width"] / 2 + 0.1, build.snap_z(), build.SNAP_HEIGHT))
    lip = lip.cut(build.cone(0))
    gap = build.gap()
    out = {}
    for kind, ring_shape in (("rail", rail), ("lip", lip)):
        ring_shape = ring_shape.cut(gap)
        for name, (a0, a1) in SEGMENTS.items():
            seg = ring_shape.intersect(_sector(a0, a1))
            if seg.vals() and seg.val().Volume() > 5:
                out[f"{kind}_{name}"] = seg
    return out


def main():
    build.OUT.mkdir(parents=True, exist_ok=True)
    bed = build.P["bed"]
    print(f"{'piece':<10}{'flat size mm':<16}{'stretch min/max':<18}{'g':>6}  bed")
    parts = flat_parts()
    for name, (pat, body) in parts.items():
        bb = body.val().BoundingBox()
        fits = sorted([bb.xlen, bb.ylen]) <= sorted(bed[:2])
        g = body.val().Volume() / 1000 * build.P["density_g_cc"]
        cq.exporters.export(body, str(build.OUT / f"flat_skin_{name}.stl"))
        print(f"flat_{name:<5}{bb.xlen:6.0f} x {bb.ylen:<6.0f}  {pat.stretch[0]:.3f} / {pat.stretch[1]:.3f}  {g:>8.1f}  {'ok' if fits else 'TOO BIG'}  (support-free: all faces horizontal or vertical)")
    seam = {n: parts[n][0].edge_frame("seam")[3] for n in parts}
    cut = {n: parts[n][0].edge_frame("cut")[3] for n in ("br", "bl")}
    print(f"seam edge lengths (must match across a joint): fr {seam['fr']:.2f} / br {seam['br']:.2f} mm, fl {seam['fl']:.2f} / bl {seam['bl']:.2f} mm, back seam br {cut['br']:.2f} / bl {cut['bl']:.2f} mm")
    print(f"bend strain of the {T} mm skin at the tightest curve: about {T / (2 * min(AI, BI)) * 100:.1f}% (TPU copes with far more)")
    print(f"\n{'segment':<18}{'bbox mm':<18}{'g':>6}  bed")
    for name, seg in hoop_segments().items():
        bb = seg.val().BoundingBox()
        dims = sorted([bb.xlen, bb.ylen])
        fits = dims <= sorted(bed[:2]) and bb.zlen <= bed[2]
        g = seg.val().Volume() / 1000 * build.P["density_g_cc"]
        cq.exporters.export(seg, str(build.OUT / f"hoop_{name}.stl"))
        print(f"hoop_{name:<13}{bb.xlen:5.0f} x {bb.ylen:<4.0f} x {bb.zlen:<4.0f} {g:>6.1f}  {'ok' if fits else 'TOO BIG'}  valid {seg.val().isValid()}")


if __name__ == "__main__":
    main()
