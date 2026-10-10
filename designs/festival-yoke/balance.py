"""Weight and balance of the whole loaded collar: mass table, centre of mass, shoulder pressure, and a search for
module angles that keep the load centred. Run: uv run --no-project --with cadquery balance.py"""
import itertools
import math

import cadquery as cq

import build
import module
import power

G = 9.81
# print fill: fraction of the solid volume that is actually plastic (thin skin prints near solid, chunky modules at ~20% infill)
FILL = {"yoke": 0.9, "diffuser": 0.9, "module": 0.5, "pod": 0.5}
# payload, grams (assumptions, change to suit): what the collar actually carries
PAYLOAD = {"cup": 360, "phone": 200, "dock": 250, "fan": 40, "pod": 80, "strip": 25}   # full cup, phone, one ear defender, fan, cell+board, strip
LIGHT = {"phone": 200, "fan": 40, "pod": 80, "strip": 25}                                # no drink, no defenders parked


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


def grams(shape, fill):
    return shape.val().Volume() / 1000 * build.P["density_g_cc"] * fill


def payload_points(cup_angle=None):
    """Payload centre of mass in each module's local frame (x outward, y along rail)."""
    _, _, _, _, z_arm = module.z_levels()
    floor_z = z_arm + 8 - module.CUP_HANG
    cup = (36 + module.cup_shift(cup_angle if cup_angle is not None else module.CUP_ANGLE) + module.CUP_ID / 2 + module.WALL, 0, floor_z + 45)
    dock = (46 + module.DOCK_CUP[1] / 2 + 3, 0, z_arm + 3 + 30)
    pod = (power.POD_X, 0, z_arm + power.WALL + power.BATT[2] / 2 + 0.5)
    return {"cup": cup, "dock": dock, "pod": pod}


def build_all():
    mods = {"cup": module.cup_module(), "phone": module.phone_module(), "dock": module.dock_module(),
            "fan": module.fan_module(), "pod": power.pod_module()}
    printed = {"yoke": (build.yoke(), FILL["yoke"]), "diffuser": (power.fitted_diffuser(), FILL["diffuser"]), "strip": (power.strip(), 0)}
    for k, m in mods.items():
        printed[k] = (m, FILL["pod" if k == "pod" else "module"])
    printed["pod lid"] = (power.pod_lid(), FILL["pod"])
    return mods, printed


def com(items):
    m = sum(i[0] for i in items)
    return m, tuple(sum(i[0] * i[1][a] for i in items) / m for a in range(3))


def loaded_com(mods_local, printed_mass, angles, payload, pay_local):
    """items: (mass g, global point) for printed parts and payload at the given module angles."""
    items = []
    for k, (mass, local) in mods_local.items():
        items.append((mass, to_global(local, angles[k])))
    for k, g in payload.items():
        if k == "strip":
            continue
        local = pay_local.get(k, mods_local[k][1])
        items.append((g, to_global(local, angles[k])))
    items.extend(printed_mass["fixed"])
    if "strip" in payload:
        items.append((payload["strip"], printed_mass["strip_com"]))
    return com(items)


def main():
    mods, printed = build_all()
    angles = {"cup": module.CUP_ANGLE, "phone": module.PHONE_ANGLE, "dock": module.DOCK_ANGLE, "fan": module.FAN_ANGLE, "pod": power.POD_ANGLE}
    print(f"{'part':<10}{'solid g':>9}{'fill':>6}{'printed g':>11}")
    fixed, total_print = [], 0.0
    mods_local = {}
    for name, (shape, fill) in printed.items():
        solid = shape.val().Volume() / 1000 * build.P["density_g_cc"]
        g = solid * fill
        total_print += g
        print(f"{name:<10}{solid:>9.0f}{fill:>6.2f}{g:>11.0f}")
        if name in mods:
            mods_local[name] = (g, to_local(center(shape), angles[name]))
        elif name == "pod lid":
            pod_g, pod_l = mods_local["pod"]
            mods_local["pod"] = (pod_g + g, pod_l)   # lid rides with the pod
        elif name != "strip":
            fixed.append((g, center(shape)))
    print(f"{'printed total':<10}{'':>15}{total_print:>11.0f}  (strip is bought, not printed)")
    pay_local = payload_points()
    printed_mass = {"fixed": fixed, "strip_com": center(printed["strip"][0])}
    full_pay = sum(PAYLOAD.values())
    light_pay = sum(LIGHT.values())
    print(f"payload: full {full_pay} g, light {light_pay} g (cup {PAYLOAD['cup']}, phone {PAYLOAD['phone']}, one defender {PAYLOAD['dock']}, cell+board {PAYLOAD['pod']}, fan {PAYLOAD['fan']}, strip {PAYLOAD['strip']})")

    def report(tag, ang):
        for label, pay in (("full", PAYLOAD), ("light", LIGHT)):
            m, c = loaded_com(mods_local, printed_mass, ang, pay, pay_local)
            off = math.hypot(c[0], c[1])
            torque = m / 1000 * G * off / 1000
            print(f"  {tag:<9}{label:<6}{m:>6.0f} g  COM x {c[0]:>6.1f}  y {c[1]:>6.1f} mm  offset {off:>5.1f} mm  tipping torque {torque:.2f} N*m")

    print("\ncentre of mass (x: + = wearer's right, y: + = front) of the loaded collar:")
    report("current", angles)
    # pressure on the foam seats
    area = 4 * build.PAD["length"] * build.PAD["width"] * 0.8 / 100        # cm2, oval ~ 0.8 of its bounding box
    m_full, _ = loaded_com(mods_local, printed_mass, angles, PAYLOAD, pay_local)
    print(f"shoulder pressure on the {area:.0f} cm2 of foam seats: {m_full / 1000 * G / area * 10:.1f} kPa full (backpack straps are typically 5-15 kPa)")

    # search: cup/phone near the front, dock/fan near a shoulder, pod at the back, with spacing so clips cannot collide
    front_gap = range(60, 121)
    def sep_ok(a):
        vals = list(a.values())
        return all(min((x - y) % 360, (y - x) % 360) >= 38 for x, y in itertools.combinations(vals, 2))
    best = []
    grid = range(0, 360, 15)
    def near_side(a, tol=45):
        return min(abs((a + 180) % 360 - 180), abs((a - 180 + 180) % 360 - 180)) <= tol

    for cup, phone in itertools.product((40, 55, 70), (110, 125, 140)):
        for dock, fan, pod in itertools.product(grid, grid, grid):
            # reachable and sensible: dock and fan sit near a shoulder (fan must see the face), pod at the back
            if not (near_side(dock) and near_side(fan) and 225 <= pod <= 315):
                continue
            ang = {"cup": cup, "phone": phone, "dock": dock, "fan": fan, "pod": pod}
            if not sep_ok(ang):
                continue
            score = 0.0
            for pay in (PAYLOAD, LIGHT):
                _, c = loaded_com(mods_local, printed_mass, ang, pay, pay_local)
                score += c[0] ** 2 + c[1] ** 2
            # the dock must be reachable: near a side (0 or 180 deg); the fan must aim at the face from the sides or front
            best.append((score, ang))
    best.sort(key=lambda t: t[0])
    print("\nbest layouts by balance (full and light loads), dock and fan within 45 deg of a shoulder, pod at the back:")
    for score, ang in best[:5]:
        print(f"  score {score:7.0f}  {ang}")
    print("\nbest layout:")
    report("proposed", best[0][1])
    return best[0][1]


if __name__ == "__main__":
    main()
