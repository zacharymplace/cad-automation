"""Clip-on modules for the shoulder rail: a cup cradle (front-right) and a phone cradle (front-left).
Both snap onto the T-rail through the same clip. Run: uv run --no-project --with cadquery module.py"""
import math

import cadquery as cq

import build

R = build.R
CLEAR = 0.3          # gap round the rail inside the pocket
LENGTH = 56          # clip length along the rail; longer clip = less prying under a load
SCREW_Y = 18         # M3 retention screws sit this far either side of centre

# cup cradle
CUP_ID, WALL, RING_H = 80, 2.4, 40
CUP_ANGLE = 55       # deg on the rail, 0 = right side, 90 = front
CUP_HANG = 110       # how far the cup floor hangs below the clip
CUP_OPEN = 52        # width of the side opening in the cup ring

# phone cradle (snap-in from the wearer side, open back window for the camera)
PHONE_ANGLE = 125
PHONE_W, PHONE_H, PHONE_T = 84, 165, 14     # phone in its case
PHONE_TILT = 8       # deg, top leans outward so the screen faces up toward the eyes
PHONE_GAP = 38       # distance from the rail line to the cradle's lowest inner edge


def pose(angle: float):
    """Point on the rail ellipse and the outward-normal heading there."""
    a, b, zs = build.surface(R["position"])
    t = math.radians(angle)
    return a * math.cos(t), b * math.sin(t), zs, math.degrees(math.atan2(a * math.sin(t), b * math.cos(t)))


def z_levels():
    _, _, zs, _ = pose(0)
    stem_top = zs + R["stem_height"]
    cap_top = stem_top + R["cap_height"]
    return zs, zs + 3.0, stem_top, cap_top, cap_top + CLEAR + 2.2     # zs, zb (clip underside), stem_top, cap_top, z_arm


def clip_local():
    """Clip body in the local frame: x = outward normal, y = along the rail, origin on the rail line."""
    zs, zb, _, _, z_arm = z_levels()
    base = cq.Workplane("XY").box(14, LENGTH, 7.5, centered=(False, True, False)).translate((-5, 0, zb))
    top = cq.Workplane("XY").box(22, 40, 8, centered=(True, True, False)).translate((0, 0, z_arm))
    return base.union(top)


def mount(local: cq.Workplane, angle: float) -> cq.Workplane:
    """Place a local-frame module on the rail at `angle`, then cut the rail pocket, screw holes and skin trim."""
    px, py, zs, heading = pose(angle)
    _, zb, stem_top, _, _ = z_levels()
    u = R["position"]
    m = local.rotate((0, 0, 0), (0, 0, 1), heading).translate((px, py, 0))
    stem = build.ring(u, R["stem_width"] / 2 + CLEAR, R["stem_width"] / 2 + CLEAR, zb - 1, stem_top - zb + 1 - 0.3)
    cap = build.ring(u, R["cap_width"] / 2 + CLEAR, R["cap_width"] / 2 + CLEAR, stem_top - 0.3, R["cap_height"] + 2 * CLEAR)
    m = m.cut(stem).cut(cap)
    for y in (-SCREW_Y, SCREW_Y):  # M3 pilot holes from the outer face into the stem channel
        pilot = cq.Workplane("YZ").workplane(offset=-2).center(y, stem_top - 2).circle(1.3).extrude(14)
        m = m.cut(pilot.rotate((0, 0, 0), (0, 0, 1), heading).translate((px, py, 0)))
    return m.cut(build.cone(0).translate((0, 0, 0.3)))  # skin is steeper toward the front: trim to 0.3 mm above it


def cup_module(angle: float = CUP_ANGLE) -> cq.Workplane:
    _, _, _, _, z_arm = z_levels()
    arm = cq.Workplane("XY").box(38, 20, 8, centered=(False, True, False)).translate((0, 0, z_arm))
    xr = 36 + CUP_ID / 2 + WALL
    floor_z = z_arm + 8 - CUP_HANG
    post = cq.Workplane("XY").box(10, 14, z_arm + 8 - floor_z + 3, centered=(False, True, False)).translate((27, 0, floor_z - 3))
    ring = cq.Workplane("XY").workplane(offset=floor_z - 3).center(xr, 0).circle(CUP_ID / 2 + WALL).extrude(RING_H)
    ring = ring.cut(cq.Workplane("XY").workplane(offset=floor_z).center(xr, 0).circle(CUP_ID / 2).extrude(RING_H))
    ring = ring.cut(cq.Workplane("XY").workplane(offset=floor_z - 4).center(xr, 0).circle(CUP_ID / 2 - 14).extrude(6))  # open floor
    ring = ring.cut(cq.Workplane("XY").box(30, CUP_OPEN, RING_H, centered=(False, True, False)).translate((xr + 6, 0, floor_z)))
    return mount(clip_local().union(arm).union(post).union(ring), angle)


def phone_module(angle: float = PHONE_ANGLE) -> cq.Workplane:
    _, _, _, _, z_arm = z_levels()
    iw, it = PHONE_W + 2, PHONE_T + 0.5          # interior width / depth, with a little slack
    ow = iw + 2 * 4                              # overall width
    frame_h = PHONE_H + 8
    # cradle in its own frame: bottom centre at the origin, plate at +x (outer), open toward -x (wearer), z up
    plate = cq.Workplane("XY").box(3, ow, frame_h, centered=(False, True, False)).translate((0, 0, 0))
    plate = plate.cut(cq.Workplane("XY").box(8, iw - 22, frame_h - 30, centered=(True, True, False)).translate((1.5, 0, 15)))  # camera / grip window
    def wall(s):
        w = cq.Workplane("XY").box(it + 2, 2.5, frame_h, centered=(False, True, False)).translate((-it - 2, s * (iw / 2 + 1.25), 0))
        win = cq.Workplane("XY").box(it - 1, 8, frame_h - 60, centered=(False, True, False)).translate((-it, s * (iw / 2 + 1.25), 30))
        return w.cut(win)
    lip = lambda s: cq.Workplane("XY").box(2, 7, frame_h - 10, centered=(False, True, False)).translate((-it - 2, s * (iw / 2 - 1.5), 5))
    shelf = cq.Workplane("XY").box(it + 5, iw + 8, 4, centered=(False, True, False)).translate((-it - 2, 0, 0))
    shelf_lip = cq.Workplane("XY").box(2, iw - 10, 10, centered=(False, True, False)).translate((-it - 2, 0, 0))
    top = cq.Workplane("XY").box(it + 5, ow, 6, centered=(False, True, False)).translate((-it - 2, 0, frame_h - 6))
    cradle = plate.union(wall(1)).union(wall(-1)).union(lip(1)).union(lip(-1)).union(shelf).union(shelf_lip).union(top)
    cradle = cradle.rotate((0, 0, 0), (0, 1, 0), PHONE_TILT)
    # lowest, innermost point after tilt sits PHONE_GAP out from the rail line; top is held at the arm
    tilt = math.radians(PHONE_TILT)
    tx = PHONE_GAP + it + 2
    tz = z_arm + 8 - frame_h * math.cos(tilt)
    cradle = cradle.translate((tx, 0, tz))
    top_x = tx + frame_h * math.sin(tilt)
    arm = cq.Workplane("XY").box(top_x + 4, 20, 8, centered=(False, True, False)).translate((0, 0, z_arm))
    return mount(clip_local().union(arm).union(cradle), angle)


def torso(grow: float = 0.0) -> cq.Workplane:
    """Mannequin torso below the collar (same numbers as view.py), for clash checks."""
    return cq.Workplane("XY").workplane(offset=-300).ellipse(build.AO + 10 + grow, build.BO - 5 + grow).extrude(300 - build.DROP - 3.5)


def report(name: str, m: cq.Workplane):
    def clash(other):
        c = m.intersect(other)
        return sum(s.Volume() for s in c.solids().vals()) if c.vals() else 0.0

    bb = m.val().BoundingBox()
    print(f"{name}: bbox {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm, solid {m.val().Volume() / 1000 * build.P['density_g_cc']:.0f} g, solids {len(m.solids().vals())}")
    print(f"  clash: yoke {clash(build.yoke()):.2f} mm3, torso {clash(torso()):.2f}, torso+8mm {clash(torso(8)):.2f} (want 0, 0, ~0)")
    print(f"  lowest point {-bb.zmin:.0f} mm below neck edge")


def main():
    build.OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("module_cup", cup_module), ("module_phone", phone_module)):
        m = fn()
        cq.exporters.export(m, str(build.OUT / f"{name}.stl"))
        report(name, m)


if __name__ == "__main__":
    main()
