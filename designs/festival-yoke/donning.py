"""Putting-on and taking-off checks: can one hand get the collar over the head, and can the modules be fitted?

    uv run --no-project --with cadquery donning.py            head passage, spread force, rail-clip fit force
    uv run --no-project --with cadquery donning.py --modules  also checks the kit's modules against the head's path

These are geometry and beam estimates with stated assumptions: they find problems, they do not certify a fit.
"""
import math
import sys

import numpy as np

import build
import layout
import sizing

E_TPU, E_PETG = 26.0, 2000.0       # MPa (95A TPU, PETG); check your datasheets
HAND_COMFORT_N = 15.0              # a push or pull a weak one-handed grip can usually manage, rough
HEAD_H = 115.0                     # half height of the head ellipsoid used in the mannequin


def head_passage():
    """Smallest front opening the head's silhouette needs, and how far the collar must spread."""
    p, q = sizing.head_axes(build.W["head_circumference"])
    ai, bi = build.AI, build.BI
    gap = build.Y["front_gap"]
    # the head goes down through the collar plane with its silhouette (an ellipse p x q); slide it forward just far
    # enough that its back clears the back of the opening, then the front must leave through the gap
    shift = max(0.0, q - bi)
    yf = bi                                                     # where the opening ellipse crosses the centre line
    half = p * math.sqrt(max(0.0, 1 - ((yf - shift) / q) ** 2)) # head half-width where it crosses the front edge
    need = 2 * half
    side_clear = ai - p                                         # sideways room each side
    return {"head": (2 * p, 2 * q), "opening": (2 * ai, 2 * bi), "shift": shift, "need_gap": need, "gap": gap,
            "spread": max(0.0, need - gap), "side_clear": side_clear}


def spread_force(spread: float):
    """Force on each front tip to open the gap by `spread` mm, from a 2D frame model of the ring (skin + rail + lip)."""
    n = 120
    a, b, _ = build.surface(0.5)
    g = build.Y["front_gap"] / 2 + 2
    th_r = math.acos(min(0.999, g / a))
    th = np.linspace(th_r, th_r - (2 * math.pi - 2 * (math.pi / 2 - th_r)), n + 1)   # right tip round the back to the left tip
    x, y = a * np.cos(th), b * np.sin(th)
    ah, bh = build.AI + build.K if hasattr(build, "K") else build.AI + 6, build.BI + 6

    def plan_width(t):
        ro = 1 / math.sqrt((math.cos(t) / build.AO) ** 2 + (math.sin(t) / build.BO) ** 2)
        rh = 1 / math.sqrt((math.cos(t) / ah) ** 2 + (math.sin(t) / bh) ** 2)
        return ro - rh

    t_skin = build.Y["thickness"] / math.cos(math.radians(30))
    R_, G_ = build.R, build.G
    I_rail = R_["stem_height"] * R_["stem_width"] ** 3 / 12 + R_["cap_height"] * R_["cap_width"] ** 3 / 12
    A_rail = R_["stem_height"] * R_["stem_width"] + R_["cap_height"] * R_["cap_width"]
    I_lip = G_["lip_height"] * G_["lip_width"] ** 3 / 12
    A_lip = G_["lip_height"] * G_["lip_width"]
    ndof = 3 * (n + 1)
    K = np.zeros((ndof, ndof))
    for e in range(n):
        dx, dy = x[e + 1] - x[e], y[e + 1] - y[e]
        L = math.hypot(dx, dy)
        c, s = dx / L, dy / L
        tm = (th[e] + th[e + 1]) / 2
        w = plan_width(tm)
        EI = E_TPU * (t_skin * w ** 3 / 12) + E_PETG * (I_rail + I_lip)
        EA = E_TPU * t_skin * w + E_PETG * (A_rail + A_lip)
        kl = np.array([
            [EA / L, 0, 0, -EA / L, 0, 0],
            [0, 12 * EI / L ** 3, 6 * EI / L ** 2, 0, -12 * EI / L ** 3, 6 * EI / L ** 2],
            [0, 6 * EI / L ** 2, 4 * EI / L, 0, -6 * EI / L ** 2, 2 * EI / L],
            [-EA / L, 0, 0, EA / L, 0, 0],
            [0, -12 * EI / L ** 3, -6 * EI / L ** 2, 0, 12 * EI / L ** 3, -6 * EI / L ** 2],
            [0, 6 * EI / L ** 2, 2 * EI / L, 0, -6 * EI / L ** 2, 4 * EI / L]])
        Tm = np.zeros((6, 6))
        rot = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
        Tm[:3, :3] = rot
        Tm[3:, 3:] = rot
        kg = Tm.T @ kl @ Tm
        idx = np.r_[3 * e:3 * e + 3, 3 * (e + 1):3 * (e + 1) + 3]
        K[np.ix_(idx, idx)] += kg
    mid = int(np.argmin(np.abs(th + math.pi / 2)))             # the back of the ring
    prescribed = {3 * 0: spread / 2, 3 * n: -spread / 2, 3 * mid: 0.0, 3 * mid + 1: 0.0, 3 * mid + 2: 0.0}
    free = [d for d in range(ndof) if d not in prescribed]
    pres = np.array(list(prescribed.values()))
    pidx = list(prescribed)
    u = np.zeros(ndof)
    u[pidx] = pres
    u[free] = np.linalg.solve(K[np.ix_(free, free)], -K[np.ix_(free, pidx)] @ pres)
    f = K @ u
    # peak plan-bending strain in the skin: curvature change times half the plan width
    curv = []
    for e in range(n):
        dth = u[3 * (e + 1) + 2] - u[3 * e + 2]
        L = math.hypot(x[e + 1] - x[e], y[e + 1] - y[e])
        curv.append(abs(dth) / L * plan_width((th[e] + th[e + 1]) / 2) / 2)
    return abs(f[3 * 0]), max(curv)


def slide_on():
    """Putting a module on: slide the clip along the straight bar; a printed flexure detent clicks into a dimple."""
    import dock
    pocket = build.R["cap_width"] + 2 * 0.3
    return {"travel": dock.TRAVEL, "bar": dock.BAR_LENGTH, "slack": 0.3, "plunger_n": 3.0, "pocket": pocket}


def main():
    hp = head_passage()
    print(f"size {build.SIZE}: head about {hp['head'][0]:.0f} wide x {hp['head'][1]:.0f} long; collar opening {hp['opening'][0]:.0f} x {hp['opening'][1]:.0f}, front gap {hp['gap']:.0f}")
    print(f"  sideways room {hp['side_clear']:.0f} mm each side; head must sit {hp['shift']:.0f} mm forward of the collar centre as it passes")
    print(f"  the front must open to about {hp['need_gap']:.0f} mm: spread {hp['spread']:.0f} mm")
    F, eps = spread_force(hp["spread"])
    verdict = "within" if F <= HAND_COMFORT_N else "ABOVE"
    print(f"  estimated force on each front tip to open it: {F:.1f} N ({F / G:.2f} kgf), {verdict} what a weak one-handed grip manages ({HAND_COMFORT_N:.0f} N); peak skin strain {eps * 100:.0f}%")
    print("  (2D ring model, upper-bound stiffness: the segments and seams will make it softer; measure it with a spring scale in Stage 2)")

    print("  the bare collar (flat skin plus rail and lip segments) is roughly 150 g printed: light enough to lift one-handed; fit modules AFTER it is on")

    s = slide_on()
    ok = s["plunger_n"] <= HAND_COMFORT_N
    print(f"\nmodule attach: slide the clip onto the {s['bar']} mm straight bar from its open end ({s['slack']} mm slack each side), with {s['travel']} mm of travel each way")
    print(f"  push needed: the printed detent's click, about {s['plunger_n']:.0f} N (tongue force about 2 N plus friction), plus a little more: {'within' if ok else 'ABOVE'} one-handed reach ({HAND_COMFORT_N:.0f} N)")
    print("  a module cannot lift straight off (T-slot), so it cannot fall off by accident; it comes off by sliding it out of the open end")
    print("  the old snap-on clip would have needed about 2,000 N per side: replaced")
    print("  open question: a printed 80 mm bar must be straight to within about 0.3 mm or the clip will bind: check in the clip coupon test")

    if "--modules" in sys.argv:
        modules_vs_head(hp)


G = 9.81


def modules_vs_head(hp):
    import cadquery as cq

    import kit
    p, q = hp["head"][0] / 2, hp["head"][1] / 2
    cyl = cq.Workplane("XY").workplane(offset=-400).center(0, hp["shift"]).ellipse(p, q).extrude(900)
    print(f"\nmodules of kit {layout.KIT} against the head's path through the collar (head silhouette pushed down through it):")
    worst = 0.0
    for name, shape in kit.modules().items():
        c = shape.intersect(cyl)
        v = sum(s.Volume() for s in c.solids().vals()) if c.vals() else 0.0
        worst = max(worst, v)
        print(f"  {name:<6}{'blocks the head' if v > 1 else 'clear'}{f' ({v:.0f} mm3)' if v > 1 else ''}")
    print("every module clears the head's path" if worst <= 1 else "some modules sit in the head's path: move them or fit them after the collar is on")


if __name__ == "__main__":
    main()
