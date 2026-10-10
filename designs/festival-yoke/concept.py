"""Concept sheet: hero view, underside pad seats, cup module, phone module -> out/<size>/concept.png
Run: uv run --no-project --with cadquery --with matplotlib concept.py"""
import math

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import build
import module
from viz import COLORS, mannequin, shade, tris_of

comps = build.components()
extras = {"cup": module.cup_module(), "phone": module.phone_module(), "diffuser": build.diffuser()}


PENDING = {}


def add(ax, shape, color, alpha=1.0):
    """Queue a shape; flush() draws all of an axes' shapes as one collection so triangles depth-sort together."""
    tr = tris_of(shape)
    PENDING.setdefault(ax, []).append((tr, shade(tr, color, alpha)))


def flush():
    for ax, items in PENDING.items():
        tr = np.concatenate([t for t, _ in items])
        fc = [c for _, cs in items for c in cs]
        ax.add_collection3d(Poly3DCollection(tr, facecolors=fc, edgecolor="none"))


def frame(ax, centre, span, el, az, title):
    cx, cy, cz = centre
    ax.set_xlim(cx - span, cx + span); ax.set_ylim(cy - span, cy + span); ax.set_zlim(cz - span, cz + span)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(el, az); ax.set_axis_off()
    ax.set_title(title, color="#e8e8ee", fontsize=11, family="monospace")


fig = plt.figure(figsize=(15, 11), facecolor="#14141a")

ax = fig.add_subplot(2, 2, 1, projection="3d", facecolor="#14141a")
mannequin(ax)
for k in ("skin", "rail", "lip"):
    add(ax, comps[k], COLORS[k])
add(ax, extras["cup"], COLORS["module"]); add(ax, extras["phone"], COLORS["module"])
add(ax, extras["diffuser"], COLORS["diffuser"], 0.55)
frame(ax, (0, 0, 80), 215, 22, 78, "everything on: yoke, LED cover, cup right, phone left")

ax = fig.add_subplot(2, 2, 2, projection="3d", facecolor="#14141a")
for k in ("rail", "lip", "skin", "pad"):  # far side first: painter's algorithm, viewed from below
    add(ax, comps[k], COLORS[k])
frame(ax, (0, 0, -20), 160, -55, 70, "from below: blue foam seats rest on the trapezius")

ax = fig.add_subplot(2, 2, 3, projection="3d", facecolor="#14141a")
mannequin(ax)
for k in ("skin", "rail", "lip"):
    add(ax, comps[k], COLORS[k])
add(ax, extras["cup"], COLORS["module"])
px, py, zs, h = module.pose(module.CUP_ANGLE)
frame(ax, (px + 40, py + 40, -60), 130, 18, 40, "cup cradle: slides out sideways toward the hand")

ax = fig.add_subplot(2, 2, 4, projection="3d", facecolor="#14141a")
mannequin(ax)
for k in ("skin", "rail", "lip"):
    add(ax, comps[k], COLORS[k])
add(ax, extras["phone"], COLORS["module"])
px, py, zs, h = module.pose(module.PHONE_ANGLE)
frame(ax, (px - 30, py + 50, -80), 150, 15, 140, "phone cradle: snaps in from the wearer side, screen tilts up")

flush()
fig.suptitle(f"festival-yoke concept, size {build.SIZE}  |  nothing above the shoulders", color="#e8e8ee", fontsize=13, family="monospace")
fig.savefig(build.OUT / "concept.png", dpi=105, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("wrote", build.OUT / "concept.png")
