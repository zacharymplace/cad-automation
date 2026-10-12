"""Weight and balance of the loaded collar for the active kit, and a search for module angles that keep it centred.

    uv run --no-project --with cadquery balance.py            report the active kit (FESTIVAL_YOKE_KIT=glow to pick)
    uv run --no-project --with cadquery balance.py --tune     tune every kit, write kits.toml, print one table
"""
import itertools
import json
import math
import os
import subprocess
import sys

import build
import kit
import layout
import module
import power

G = 9.81
# print fill: fraction of the solid volume that is actually plastic (thin skin prints near solid, chunky modules ~20% infill)
FILL = {"yoke": 0.9, "diffuser": 0.9, "module": 0.5}
# payload, grams (assumptions, change to suit): what the collar actually carries
PAYLOAD = {"cup": 360, "phone": 200, "dock": 250, "fan": 40, "pod": 80, "id": 20, "tube": 30, "strip": 25}
LIGHT = {"phone": 200, "fan": 40, "pod": 80, "id": 20, "strip": 25}          # no drink, no defenders parked
SEP = 38                                                                       # min degrees between clips


def near_side(a, tol=45):
    return min(abs((a + 180) % 360 - 180), abs((a - 180 + 180) % 360 - 180)) <= tol


ALL = range(0, 360, 15)
CANDIDATES = {
    "cup": (25, 40, 55, 70), "phone": (125, 140, 155, 170), "id": (0, 15, 30, 45, 60, 120, 135, 150, 165, 180), "tube": (0, 15, 30, 45, 60),
    "dock": [a for a in ALL if near_side(a) and not 60 <= a <= 120], "fan": [a for a in ALL if near_side(a) and not 60 <= a <= 120],
    "pod": [a for a in ALL if 225 <= a <= 315],
}


def center(shape):
    c = shape.val().Center()
    return (c.x, c.y, c.z)


def to_local(g, angle):
    px, py, _, h = module.pose(angle)
    c, s = math.cos(math.radians(h)), math.sin(math.radians(h))
    dx, dy = g[0] - px, g[1] - py
    return (dx * c + dy * s, -dx * s + dy * c, g[2])


def to_global(l, angle):
    px, py, _, h = module.pose(angle)
    c, s = math.cos(math.radians(h)), math.sin(math.radians(h))
    return (px + l[0] * c - l[1] * s, py + l[0] * s + l[1] * c, l[2])


def solid_g(shape):
    return shape.val().Volume() / 1000 * build.P["density_g_cc"]


def payload_local():
    """Payload centre of mass in the module's local frame where the module's own centre is a poor guess."""
    _, _, _, _, z_arm = module.z_levels()
    floor_z = z_arm + 8 - module.CUP_HANG
    return {
        "cup": (36 + module.cup_shift(module.CUP_ANGLE) + module.CUP_ID / 2 + module.WALL, 0, floor_z + 45),
        "dock": (46 + module.DOCK_CUP[1] / 2 + 3, 0, z_arm + 3 + 30),
        "pod": (power.POD_X, 0, z_arm + power.WALL + power.BATT[2] / 2 + 0.5),
    }


def setup():
    """Printed masses and local centres for the active kit, plus the fixed (non-module) parts."""
    angles = layout.angles()
    mods = kit.modules()
    fixed, printed = [], {}
    yoke = build.yoke()
    printed["yoke"] = solid_g(yoke) * FILL["yoke"]
    fixed.append((printed["yoke"], center(yoke)))
    if layout.has_leds():
        dif = power.fitted_diffuser()
        printed["diffuser"] = solid_g(dif) * FILL["diffuser"]
        fixed.append((printed["diffuser"], center(dif)))
    local = {}
    for name, shape in mods.items():
        g = solid_g(shape) * FILL["module"]
        if name == "pod":
            g += solid_g(power.pod_lid()) * FILL["module"]
        printed[name] = g
        local[name] = (g, to_local(center(shape), angles[name]))
    pay_l = payload_local()
    strip_com = center(power.strip()) if layout.has_leds() else None
    return printed, fixed, local, pay_l, strip_com


def total(printed_fixed, local, pay_l, strip_com, angles, payload):
    items = list(printed_fixed)
    for name, (g, lc) in local.items():
        items.append((g, to_global(lc, angles[name])))
        if name in payload:
            items.append((payload[name], to_global(pay_l.get(name, lc), angles[name])))
    if strip_com is not None and "strip" in payload:
        items.append((payload["strip"], strip_com))
    m = sum(i[0] for i in items)
    return m, tuple(sum(i[0] * i[1][a] for i in items) / m for a in range(3))


def support():
    """Half-width and half-depth of the rectangle spanned by the foam seats: the centre of mass must stay inside it
    or the collar pitches or rolls and one side lifts off the shoulder."""
    a, b, _ = build.surface(build.PAD["position"])
    xs = [abs(a * math.cos(math.radians(d))) for d in build.PAD["angles"]]
    ys = [abs(b * math.sin(math.radians(d))) for d in build.PAD["angles"]]
    return min(xs), min(ys)


def offset(c):
    return math.hypot(c[0], c[1])


def torque(m, c):
    return m / 1000 * G * offset(c) / 1000


def summary(angles, setup_out):
    printed, fixed, local, pay_l, strip_com = setup_out
    out = {}
    for label, pay in (("full", PAYLOAD), ("light", LIGHT)):
        m, c = total(fixed, local, pay_l, strip_com, angles, pay)
        sx, sy = support()
        margin = min(sx - abs(c[0]), sy - abs(c[1]))
        out[label] = {"mass": round(m), "x": round(c[0], 1), "y": round(c[1], 1), "offset": round(offset(c), 1), "torque": round(torque(m, c), 2), "margin": round(margin, 1)}
    out["printed"] = round(sum(printed.values()))
    return out


def tune(setup_out):
    """Backtracking search over module angles; score = squared COM offset, full plus light payload."""
    printed, fixed, local, pay_l, strip_com = setup_out
    names = [n for n in layout.present() if n in CANDIDATES]
    if not names:
        return {}
    contrib = {}
    for n in names:
        for a in CANDIDATES[n]:
            row = {}
            for label, pay in (("full", PAYLOAD), ("light", LIGHT)):
                g, lc = local[n]
                gx, gy, _ = to_global(lc, a)
                m, mx, my = g, g * gx, g * gy
                if n in pay:
                    px, py, _ = to_global(pay_l.get(n, lc), a)
                    m, mx, my = m + pay[n], mx + pay[n] * px, my + pay[n] * py
                row[label] = (m, mx, my)
            contrib[(n, a)] = row
    base = {}
    for label, pay in (("full", PAYLOAD), ("light", LIGHT)):
        items = list(fixed)
        if strip_com is not None and "strip" in pay:
            items.append((pay["strip"], strip_com))
        base[label] = (sum(i[0] for i in items), sum(i[0] * i[1][0] for i in items), sum(i[0] * i[1][1] for i in items))
    best = (1e18, None)

    def ok(a, chosen):
        return all(min((a - b) % 360, (b - a) % 360) >= SEP for b in chosen)

    def rec(i, chosen, assign):
        nonlocal best
        if i == len(names):
            score = 0.0
            for label in ("full", "light"):
                m, mx, my = base[label]
                for n, a in assign.items():
                    c = contrib[(n, a)][label]
                    m, mx, my = m + c[0], mx + c[1], my + c[2]
                score += (mx / m) ** 2 + (my / m) ** 2
            if "dock" in assign:  # the dock should stay reachable: gently prefer a real side over behind the shoulder
                score += 0.5 * min(abs((assign["dock"] + 180) % 360 - 180), abs((assign["dock"] - 180 + 180) % 360 - 180)) ** 2 / 10
            if score < best[0]:
                best = (score, dict(assign))
            return
        n = names[i]
        for a in CANDIDATES[n]:
            if ok(a, chosen):
                assign[n] = a
                rec(i + 1, chosen + [a], assign)
                del assign[n]

    rec(0, [], {})
    return best[1] or {}


def report():
    s = setup()
    printed, fixed, local, pay_l, strip_com = s
    angles = layout.angles()
    print(f"kit {layout.KIT} ({layout.KITS[layout.KIT]['blurb']})")
    print(f"{'part':<10}{'printed g':>10}")
    for k, v in printed.items():
        print(f"{k:<10}{v:>10.0f}")
    out = summary(angles, s)
    print(f"printed total {out['printed']} g; angles {angles}")
    for label in ("full", "light"):
        o = out[label]
        flag = "inside the foam seats" if o["margin"] > 0 else f"OUTSIDE the foam seats by {-o['margin']:.0f} mm: the collar will pitch or roll"
        print(f"  {label:<6}{o['mass']:>6} g  COM x {o['x']:>6.1f} y {o['y']:>6.1f}  offset {o['offset']:>5.1f} mm  tipping torque {o['torque']:.2f} N*m  {flag}")
    return out


def tune_all():
    results = {}
    for name in layout.KITS:
        env = {**os.environ, "FESTIVAL_YOKE_KIT": name}
        env.pop("FESTIVAL_YOKE_NO_TUNED", None)
        run = subprocess.run([sys.executable, __file__, "--tune-one"], env=env, capture_output=True, text=True)
        line = [l for l in run.stdout.splitlines() if l.startswith("{")]
        if not line:
            print(f"{name}: failed\n{run.stdout}{run.stderr}")
            continue
        results[name] = json.loads(line[-1])
    toml = [f"# written by balance.py --tune for size {layout.SIZE}; angles in degrees on the rail\n"]
    for name, r in results.items():
        if r["angles"]:
            toml.append(f'["{layout.SIZE}.{name}"]')
            toml.extend(f"{k} = {v}" for k, v in r["angles"].items())
            toml.append("")
    (layout.ROOT / "kits.toml").write_text("\n".join(toml))
    sx, sy = support()
    print(f"foam seat rectangle: +-{sx:.0f} mm across, +-{sy:.0f} mm front to back; margin = distance the centre of mass has to spare (negative = outside)")
    print(f"{'kit':<9}{'modules':<34}{'printed g':>10}{'full g':>8}{'offset':>8}{'margin':>8}{'light g':>9}{'offset':>8}{'margin':>8}{'torque':>8}")
    for name, r in results.items():
        mods = ",".join(layout.KITS[name]["modules"]) or "-"
        print(f"{name:<9}{mods:<34}{r['printed']:>10}{r['full']['mass']:>8}{r['full']['offset']:>7.0f}mm{r['full']['margin']:>6.0f}mm{r['light']['mass']:>9}{r['light']['offset']:>7.0f}mm{r['light']['margin']:>6.0f}mm{r['full']['torque']:>7.2f}")
    print("\nwrote", layout.ROOT / "kits.toml")


def main():
    if "--tune" in sys.argv:
        tune_all()
        return
    if "--tune-one" in sys.argv:
        s = setup()
        best = tune(s)
        angles = {**layout.angles(), **best}
        out = summary(angles, s)
        out["angles"] = best
        print(json.dumps(out))
        return
    report()


if __name__ == "__main__":
    main()
