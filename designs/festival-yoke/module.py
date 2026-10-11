"""Clip-on modules for the shoulder rail: cup cradle (front-right), phone cradle (front-left), ear-defender dock
(right side) and fan (left side). All snap onto the T-rail through the same clip. Run: uv run --no-project --with cadquery module.py"""
import math

import cadquery as cq

import build
import layout

R = build.R
CLEAR = 0.3          # gap round the rail inside the pocket
LENGTH = 56          # clip length along the rail; longer clip = less prying under a load
SCREW_Y = 18         # M3 retention screws sit this far either side of centre

# cup cradle
CUP_ID, WALL, RING_H = 80, 2.4, 40
CUP_ANGLE = layout.angle("cup")   # deg on the rail, 0 = right side, 90 = front; balance.py tunes these per kit
CUP_HANG = 110       # how far the cup floor hangs below the clip
CUP_OPEN = 52        # width of the side opening in the cup ring

# phone cradle (snap-in from the wearer side, open back window for the camera)
PHONE_ANGLE = layout.angle("phone")
PHONE_W, PHONE_H, PHONE_T = 84, 165, 14     # phone in its case
PHONE_TILT = 8       # deg, top leans outward so the screen faces up toward the eyes
PHONE_GAP = 38       # distance from the rail line to the cradle's lowest inner edge


# ear-defender dock: a bowl that parks one ear cup on the shoulder, with strap slots and a tether eyelet
DOCK_ANGLE = layout.angle("dock")
DOCK_CUP = (100, 85)    # ear cup outline, long x short, mm (parametric: measure your defenders)
DOCK_DEPTH = 28

# small modules
ARM_T = 11     # arm thickness for the heavy-load modules (cup, dock); strength.py found 8 mm too thin under a 5 g bump
ID_ANGLE = layout.angle("id")
TUBE_ANGLE = layout.angle("tube")
BLANK_ANGLE = layout.angle("blank")
COVER_ANGLE = layout.angle("cover")
ID_CARD = (86, 54, 1.2)   # credit-card sized medical ID / info card
TUBE_OD = 9.5             # hydration tube outside diameter, mm

# fan: square frame for a 5 V fan, aimed up and inward at the face from shoulder level
FAN_ANGLE = layout.angle("fan")
FAN_SIZE, FAN_T, FAN_WALL = 80, 25, 2.7     # fan outline and thickness
FAN_ELEV = 40                               # deg above horizontal, aimed toward the wearer's face
FAN_X = 32                                  # fan centre, outward from the rail line (puts its lowest edge over the clip)


def pose(angle: float):
    """Point on the rail ellipse and the outward-normal heading there."""
    a, b, zs = build.surface(R["position"])
    t = math.radians(angle)
    return a * math.cos(t), b * math.sin(t), zs, math.degrees(math.atan2(a * math.sin(t), b * math.cos(t)))


def normal_gap(angle: float, ae: float, be: float) -> float:
    """Distance from the rail point, along the outward normal, to the ellipse with semi-axes ae, be."""
    px, py, _, h = pose(angle)
    c, s = math.cos(math.radians(h)), math.sin(math.radians(h))
    A = (c / ae) ** 2 + (s / be) ** 2
    B = 2 * (px * c / ae ** 2 + py * s / be ** 2)
    C = (px / ae) ** 2 + (py / be) ** 2 - 1
    return (-B + math.sqrt(B * B - 4 * A * C)) / (2 * A)


def edge_gap(angle: float) -> float:
    """Distance from the rail, along the outward normal, to the outside of the lip and the diffuser hook."""
    al, bl, _ = build.surface(build.LIP_U)
    reach = build.G["lip_width"] / 2 + 1.5 + 1.0          # hook thickness plus a little
    return normal_gap(angle, al + reach, bl + reach)


def torso_gap(angle: float) -> float:
    """Distance from the rail to the mannequin torso below the collar (same numbers as torso())."""
    return normal_gap(angle, build.AO + 10, build.BO - 5)


def cup_shift(angle: float) -> float:
    """How far the cup post and ring stand out: outside the lip and hook, and at least 8 mm further than the bare minimum."""
    return max(8.0, edge_gap(angle) + 4 - 27, torso_gap(angle) + 8 - 27)


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
    shift = cup_shift(angle)
    arm = cq.Workplane("XY").box(38 + shift, 20, ARM_T, centered=(False, True, False)).translate((0, 0, z_arm))
    xr = 36 + shift + CUP_ID / 2 + WALL
    floor_z = z_arm + 8 - CUP_HANG
    post = cq.Workplane("XY").box(10, 14, z_arm + 8 - floor_z + 3, centered=(False, True, False)).translate((27 + shift, 0, floor_z - 3))
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
    tx = max(PHONE_GAP, torso_gap(angle) + 8) + it + 2
    tz = z_arm + 8 - frame_h * math.cos(tilt)
    cradle = cradle.translate((tx, 0, tz))
    top_x = tx + frame_h * math.sin(tilt)
    arm = cq.Workplane("XY").box(top_x + 4, 20, 8, centered=(False, True, False)).translate((0, 0, z_arm))
    return mount(clip_local().union(arm).union(cradle), angle)


def dock_module(angle: float = DOCK_ANGLE) -> cq.Workplane:
    _, _, _, _, z_arm = z_levels()
    arm = cq.Workplane("XY").box(46, 20, ARM_T, centered=(False, True, False)).translate((0, 0, z_arm))
    arm = arm.cut(cq.Workplane("XY").workplane(offset=z_arm - 1).center(30, 0).circle(2.5).extrude(ARM_T + 2))  # tether eyelet
    L, W = DOCK_CUP
    xc = 46 + W / 2 + 3
    bowl = cq.Workplane("XY").workplane(offset=z_arm).center(xc, 0).ellipse(L / 2 + 3, W / 2 + 3).extrude(DOCK_DEPTH)
    bowl = bowl.cut(cq.Workplane("XY").workplane(offset=z_arm + 3).center(xc, 0).ellipse(L / 2, W / 2).extrude(DOCK_DEPTH))
    for sy in (-1, 1):  # velcro strap slots in the floor, either side of the cup
        bowl = bowl.cut(cq.Workplane("XY").workplane(offset=z_arm - 1).center(xc, sy * (W / 2 - 8)).slot2D(24, 4, 0).extrude(6))
    bowl = bowl.cut(cq.Workplane("XY").workplane(offset=z_arm - 1).center(xc, 0).ellipse(L / 2 - 16, W / 2 - 16).extrude(6))  # open floor, saves weight and drains
    return mount(clip_local().union(arm).union(bowl), angle)


def fan_module(angle: float = FAN_ANGLE) -> cq.Workplane:
    _, _, _, _, z_arm = z_levels()
    inner = FAN_SIZE + 0.6
    outer = inner + 2 * FAN_WALL
    frame = cq.Workplane("XY").box(outer, outer, FAN_T + 2, centered=(True, True, False))
    frame = frame.cut(cq.Workplane("XY").box(inner, inner, FAN_T + 1, centered=(True, True, False)).translate((0, 0, 2)))  # pocket, open at the outlet end
    frame = frame.cut(cq.Workplane("XY").box(inner - 9, inner - 9, 4, centered=(True, True, False)).translate((0, 0, -1)))   # intake opening, leaves a retaining lip
    frame = frame.cut(cq.Workplane("XY").box(10, 8, 8, centered=(True, True, False)).translate((0, -outer / 2, 10)))        # cable notch
    # axis (+z, the outlet) points up and toward the neck: rotating about y by theta sends z to (sin t, 0, cos t)
    theta = -(90 - FAN_ELEV)
    zc = z_arm + 8 + (outer / 2) * math.cos(math.radians(theta)) + 20
    frame = frame.rotate((0, 0, 0), (0, 1, 0), theta).translate((FAN_X, 0, zc))
    low = frame.vertices("<Z").val().Center()          # lowest corner of the tilted frame: hang the bracket from it
    bracket = cq.Workplane("XY").box(14, 18, low.z + 9 - z_arm, centered=(True, True, False)).translate((low.x + 4, 0, z_arm))
    return mount(clip_local().union(bracket).union(frame), angle)


def clip_coupon(angle: float = CUP_ANGLE) -> cq.Workplane:
    """Just the clip (no arm, no cradle): a quick fit test for the rail pocket and screw holes."""
    return mount(clip_local(), angle)


def blank_module(angle: float = BLANK_ANGLE) -> cq.Workplane:
    """The clip and a vertical plate with an M5 hole and four M3 holes: a base for your own attachments."""
    _, _, _, _, z_arm = z_levels()
    arm = cq.Workplane("XY").box(32, 20, 8, centered=(False, True, False)).translate((0, 0, z_arm))
    plate = cq.Workplane("XY").box(4, 46, 46, centered=(False, True, True)).translate((30, 0, z_arm - 10))
    plate = plate.union(cq.Workplane("XY").box(8, 20, 8, centered=(False, True, False)).translate((28, 0, z_arm)))
    cx = cq.Workplane("YZ").workplane(offset=26)
    plate = plate.cut(cx.center(0, z_arm - 10).circle(2.65).extrude(14))
    for dy in (-10, 10):
        for dz in (-10, 10):
            plate = plate.cut(cq.Workplane("YZ").workplane(offset=26).center(dy, z_arm - 10 + dz).circle(1.6).extrude(14))
    return mount(clip_local().union(arm).union(plate), angle)


def tube_module(angle: float = TUBE_ANGLE) -> cq.Workplane:
    """Snap-in C-clip for a hydration tube, standing up from the rail so the mouthpiece falls to the chin."""
    _, _, _, _, z_arm = z_levels()
    arm = cq.Workplane("XY").box(24, 20, 8, centered=(False, True, False)).translate((0, 0, z_arm))
    cx = 24 + TUBE_OD / 2 + 1.5
    ring = cq.Workplane("XY").workplane(offset=z_arm).center(cx, 0).circle(TUBE_OD / 2 + 2.2).extrude(18)
    ring = ring.cut(cq.Workplane("XY").workplane(offset=z_arm - 1).center(cx, 0).circle(TUBE_OD / 2 + 0.1).extrude(20))
    ring = ring.cut(cq.Workplane("XY").box(10, TUBE_OD * 0.7, 20, centered=(False, True, False)).translate((cx, 0, z_arm - 1)))  # snap slit, narrower than the tube
    return mount(clip_local().union(arm).union(ring), angle)


def id_module(angle: float = ID_ANGLE) -> cq.Workplane:
    """Pouch for a card (medical ID, allergy info, 'please give me space'), window facing out, with a tether eyelet."""
    _, _, _, _, z_arm = z_levels()
    cl, cw, ct = ID_CARD
    ow, oh = cl + 8, cw + 8
    x0 = max(30.0, edge_gap(angle) + 12, torso_gap(angle) + 8)   # plate stands outside the lip and clear of the body
    arm = cq.Workplane("XY").box(x0 + 2, 20, 8, centered=(False, True, False)).translate((0, 0, z_arm))
    arm = arm.cut(cq.Workplane("XY").workplane(offset=z_arm - 1).center(14, 0).circle(2.4).extrude(10))   # tether eyelet
    back = cq.Workplane("XY").box(2, ow, oh, centered=(False, True, False)).translate((x0, 0, z_arm + 8 - oh))
    pocket = ct + 1.0
    sides = cq.Workplane("XY").box(pocket + 2, ow, oh, centered=(False, True, False)).translate((x0 + 2, 0, z_arm + 8 - oh))
    sides = sides.cut(cq.Workplane("XY").box(pocket + 3, cl + 1, oh - 2, centered=(False, True, False)).translate((x0 + 2, 0, z_arm + 8 - oh + 2)))  # slot open at the top
    front = cq.Workplane("XY").box(1.6, ow, oh, centered=(False, True, False)).translate((x0 + 2 + pocket, 0, z_arm + 8 - oh))
    front = front.cut(cq.Workplane("XY").box(4, cl - 8, cw - 8, centered=(False, True, False)).translate((x0 + 2 + pocket - 1, 0, z_arm + 8 - oh + 4)))  # window
    return mount(clip_local().union(arm).union(back).union(sides).union(front), angle)


def cover_module(angle: float = COVER_ANGLE, length: float = 80) -> cq.Workplane:
    """A snap-on cap for an empty stretch of rail, so it does not catch on clothes."""
    zs, _, stem_top, cap_top, _ = z_levels()
    u = R["position"]
    body = build.ring(u, R["cap_width"] / 2 + CLEAR + 1.4, R["cap_width"] / 2 + CLEAR + 1.4, zs + 2.0, cap_top + 2.2 - (zs + 2.0))
    px, py, _, h = pose(angle)
    wedge = cq.Workplane("XY").box(60, length, 60, centered=(True, True, False)).translate((0, 0, -30))
    wedge = wedge.rotate((0, 0, 0), (0, 0, 1), h).translate((px, py, 0))
    body = body.intersect(wedge)
    stem = build.ring(u, R["stem_width"] / 2 + CLEAR, R["stem_width"] / 2 + CLEAR, zs, stem_top - zs - 0.3)
    cap = build.ring(u, R["cap_width"] / 2 + CLEAR, R["cap_width"] / 2 + CLEAR, stem_top - 0.3, R["cap_height"] + 2 * CLEAR)
    return body.cut(stem).cut(cap)


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
    import kit
    build.OUT.mkdir(parents=True, exist_ok=True)
    made = {}
    for name, shape in kit.modules().items():
        made[name] = shape
        cq.exporters.export(shape, str(build.OUT / f"module_{name}.stl"))
        report(f"module_{name}", shape)
    cq.exporters.export(clip_coupon(), str(build.OUT / "module_clip_coupon.stl"))
    names = list(made)
    worst = 0.0
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            c = made[a].intersect(made[b])
            v = sum(s.Volume() for s in c.solids().vals()) if c.vals() else 0.0
            worst = max(worst, v)
            if v:
                print(f"WARN {a} and {b} overlap by {v:.0f} mm3")
    print(f"kit {layout.KIT}: {len(names)} modules, module-to-module overlap {worst:.0f} mm3 worst case (want 0)")


if __name__ == "__main__":
    main()
