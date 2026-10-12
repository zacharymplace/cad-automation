"""Geometry numbers for the safety review (SAFETY.md): how far each module sticks out, what the pod sits near, neck
clearance, guard openings. Run: uv run --no-project --with cadquery safety.py"""
import math

import numpy as np

import build
import kit
import layout
import module
import power


def verts(shape):
    v, _ = shape.val().tessellate(1.5)
    return np.array([[p.x, p.y, p.z] for p in v])


def beyond_rim(pts):
    """Plan distance of each point beyond the collar's outer edge (negative inside), mm."""
    ang = np.arctan2(pts[:, 1], pts[:, 0])
    r = np.hypot(pts[:, 0], pts[:, 1])
    ro = 1 / np.sqrt((np.cos(ang) / build.AO) ** 2 + (np.sin(ang) / build.BO) ** 2)
    return r - ro


def main():
    print(f"size {build.SIZE}, kit {layout.KIT}\n")
    print(f"{'module':<8}{'beyond rim':>11}{'lowest':>8}{'highest':>9}   (mm; rim = the collar's outer edge, heights vs the neck edge)")
    mods = kit.modules()
    for name, shape in mods.items():
        p = verts(shape)
        print(f"{name:<8}{beyond_rim(p).max():>11.0f}{p[:, 2].min():>8.0f}{p[:, 2].max():>9.0f}")
    if "pod" in mods:
        p = verts(mods["pod"])
        neck = np.hypot(p[:, 0], p[:, 1]).min()
        rear = (-p[:, 1]).max() - build.BO
        print(f"\npower pod: nearest point {neck:.0f} mm from the neck axis (neck radius {build.W['neck_circumference'] / (2 * math.pi):.0f} mm), "
              f"lowest point {p[:, 2].min():.0f} mm vs the neck edge, rear edge {rear:+.0f} mm from the collar rim")
    r_neck = build.W["neck_circumference"] / (2 * math.pi)
    print(f"\nneck: opening is {build.AI - r_neck:.0f} mm (sides) and {build.BI - r_neck:.0f} mm (front-back) clear of the neck all round, with a {build.Y['front_gap']:.0f} mm gap at the front: the collar is an open C, it cannot close on the neck")
    print(f"fan guards: grid gaps {module.FAN_GUARD_PITCH - module.FAN_GUARD_BAR:.1f} mm on the intake (built in) and on the outlet (screw-on plate)")
    heavy = max((s.val().Volume() / 1000 * build.P['density_g_cc'] * 0.5, n) for n, s in mods.items()) if mods else None
    if heavy:
        print(f"heaviest printed module {heavy[1]}: about {heavy[0]:.0f} g")


if __name__ == "__main__":
    main()
