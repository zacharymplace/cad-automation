"""Clip-on cup cradle for the shoulder rail. Sits front-right on the collar, ring hangs at upper-chest height
with an open side so the cup slides out toward the hand. Snaps down onto the T-rail.
Run: uv run --no-project --with cadquery module.py"""
import math

import cadquery as cq

import build

R = build.R
CLEAR = 0.3          # gap round the rail inside the pocket
LENGTH = 56          # clip length along the rail; longer clip = less prying under a full cup
CUP_ID, WALL, RING_H = 80, 2.4, 40
ANGLE = 55           # where on the rail (deg, 0 = right side, 90 = front)
HANG = 110           # how far the cup floor hangs below the clip
SCREW_Y = 18         # M3 retention screws sit this far either side of centre
OPEN = 52            # width of the side opening in the cup ring


def pose():
    """Point on the rail ellipse and the outward-normal heading there."""
    a, b, zs = build.surface(R["position"])
    t = math.radians(ANGLE)
    px, py = a * math.cos(t), b * math.sin(t)
    heading = math.degrees(math.atan2(a * math.sin(t), b * math.cos(t)))
    return px, py, zs, heading


def cup_module() -> cq.Workplane:
    px, py, zs, heading = pose()
    u = R["position"]
    zb = zs + 3.0                       # underside of the clip, clear of the sloping skin
    stem_top = zs + R["stem_height"]
    cap_top = stem_top + R["cap_height"]
    z_arm = cap_top + CLEAR + 2.2

    # local frame: x = outward normal, y = along the rail, origin on the rail line
    # outer wall is thick (x to +9) so M3 self-tapping screws can bite the rail stem
    base = cq.Workplane("XY").box(14, LENGTH, 7.5, centered=(False, True, False)).translate((-5, 0, zb))
    top = cq.Workplane("XY").box(22, 40, 8, centered=(True, True, False)).translate((0, 0, z_arm))
    arm = cq.Workplane("XY").box(30, 20, 8, centered=(False, True, False)).translate((0, 0, z_arm))
    xr = 28 + CUP_ID / 2 + WALL
    floor_z = z_arm + 8 - HANG
    post = cq.Workplane("XY").box(10, 14, z_arm + 8 - floor_z + 3, centered=(False, True, False)).translate((19, 0, floor_z - 3))
    ring = cq.Workplane("XY").workplane(offset=floor_z - 3).center(xr, 0).circle(CUP_ID / 2 + WALL).extrude(RING_H)
    ring = ring.cut(cq.Workplane("XY").workplane(offset=floor_z).center(xr, 0).circle(CUP_ID / 2).extrude(RING_H))
    ring = ring.cut(cq.Workplane("XY").workplane(offset=floor_z - 4).center(xr, 0).circle(CUP_ID / 2 - 14).extrude(6))  # open floor
    ring = ring.cut(cq.Workplane("XY").box(30, OPEN, RING_H, centered=(False, True, False)).translate((xr + 6, 0, floor_z)))  # side opening
    m = base.union(top).union(arm).union(post).union(ring)
    m = m.rotate((0, 0, 0), (0, 0, 1), heading).translate((px, py, 0))

    # pocket follows the curved rail exactly: stem channel below, cap pocket above, lips between
    stem = build.ring(u, R["stem_width"] / 2 + CLEAR, R["stem_width"] / 2 + CLEAR, zb - 1, stem_top - zb + 1 - 0.3)
    cap = build.ring(u, R["cap_width"] / 2 + CLEAR, R["cap_width"] / 2 + CLEAR, stem_top - 0.3, R["cap_height"] + 2 * CLEAR)
    m = m.cut(stem).cut(cap)
    for y in (-SCREW_Y, SCREW_Y):  # M3 pilot holes from the outer face into the stem channel
        pilot = cq.Workplane("YZ").workplane(offset=-2).center(y, stem_top - 2).circle(1.3).extrude(14)
        m = m.cut(pilot.rotate((0, 0, 0), (0, 0, 1), heading).translate((px, py, 0)))
    # the skin is steeper toward the front, so trim everything within 0.3 mm of the collar surface
    return m.cut(build.cone(0).translate((0, 0, 0.3)))


def torso() -> cq.Workplane:
    """Mannequin torso below the collar (same numbers as view.py), for a clash check."""
    return cq.Workplane("XY").workplane(offset=-300).ellipse(build.AO + 10, build.BO - 5).extrude(300 - build.DROP - 3.5)


def main():
    m = cup_module()

    def clash(other):
        c = m.intersect(other)
        return sum(s.Volume() for s in c.solids().vals()) if c.vals() else 0.0

    bb = m.val().BoundingBox()
    cq.exporters.export(m, str(build.OUT / "module_cup.stl"))
    print(f"module_cup: bbox {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm, solid {m.val().Volume() / 1000 * build.P['density_g_cc']:.0f} g, solids {len(m.solids().vals())}")
    print(f"clash with yoke {clash(build.yoke()):.2f} mm3, with torso {clash(torso()):.2f} mm3 (want 0 for both)")
    print(f"cup floor {-bb.zmin:.0f} mm below neck edge; clip top {bb.zmax:.0f} mm above it; reaches {max(abs(bb.xmax), abs(bb.xmin)):.0f} mm sideways, {bb.ymax:.0f} mm forward")


if __name__ == "__main__":
    main()
