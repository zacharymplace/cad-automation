"""Concept sheet: hero view, underside pad seats, cup module, phone module -> out/<size>/concept.png
Run: uv run --no-project --with cadquery --with matplotlib concept.py"""
import math

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import build
import module
import power
from viz import COLORS, mannequin, shade, tris_of

comps = build.components()
extras = {"cup": module.cup_module(), "phone": module.phone_module(), "dock": module.dock_module(), "fan": module.fan_module(), "pod": power.pod_module(), "lid": power.pod_lid(), "id": module.id_module(), "tube": module.tube_module(), "strip": power.strip(), "diffuser": power.fitted_diffuser()}


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
for k in [k for k in ("skin", "rail", "lip") if k in comps]:
    add(ax, comps[k], COLORS[k])
for k in ("cup", "phone", "dock", "fan", "pod", "lid", "id", "tube"):
    add(ax, extras[k], COLORS["module"])
add(ax, extras["strip"], COLORS["strip"])
add(ax, extras["diffuser"], COLORS["diffuser"], 0.5)
frame(ax, (0, 0, 80), 230, 22, 78, "full kit: carry, comfort and glow modules")

ax = fig.add_subplot(2, 2, 2, projection="3d", facecolor="#14141a")
for k in [k for k in ("rail", "lip", "skin", "pad") if k in comps]:  # far side first: painter's algorithm, viewed from below
    add(ax, comps[k], COLORS[k])
frame(ax, (0, 0, -20), 160, -55, 70, "from below: blue foam seats rest on the trapezius")

ax = fig.add_subplot(2, 2, 3, projection="3d", facecolor="#14141a")
mannequin(ax)
for k in [k for k in ("skin", "rail", "lip") if k in comps]:
    add(ax, comps[k], COLORS[k])
add(ax, extras["cup"], COLORS["module"])
px, py, zs, h = module.pose(module.CUP_ANGLE)
frame(ax, (px + 40, py + 40, -60), 130, 18, 40, "cup cradle: slides out sideways toward the hand")

ax = fig.add_subplot(2, 2, 4, projection="3d", facecolor="#14141a")
mannequin(ax)
for k in [k for k in ("skin", "rail", "lip") if k in comps]:
    add(ax, comps[k], COLORS[k])
add(ax, extras["phone"], COLORS["module"])
px, py, zs, h = module.pose(module.PHONE_ANGLE)
frame(ax, (px - 30, py + 50, -80), 150, 15, 140, "phone cradle: snaps in from the wearer side, screen tilts up")

flush()
fig.suptitle(f"festival-yoke concept, size {build.SIZE}  |  nothing above the shoulders", color="#e8e8ee", fontsize=13, family="monospace")
fig.savefig(build.OUT / "concept.png", dpi=105, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("wrote", build.OUT / "concept.png")


# second sheet: ear-defender dock and fan
fig = plt.figure(figsize=(15, 6.5), facecolor="#14141a")
for i, (key, angle, title, el, az, off) in enumerate([
    ("dock", module.DOCK_ANGLE, "ear-defender dock (right shoulder)", 28, 20, (60, 0, -10)),
    ("fan", module.FAN_ANGLE, "80 mm fan aimed at the face (left shoulder)", 22, 200, (-60, 0, 30)),
]):
    ax = fig.add_subplot(1, 2, i + 1, projection="3d", facecolor="#14141a")
    mannequin(ax)
    for k in [k for k in ("skin", "rail", "lip") if k in comps]:
        add(ax, comps[k], COLORS[k])
    add(ax, extras[key], COLORS["module"])
    px, py, zs, h = module.pose(angle)
    frame(ax, (px + off[0], py + off[1], zs + off[2]), 140, el, az, title)
flush()
fig.suptitle(f"festival-yoke modules, size {build.SIZE}", color="#e8e8ee", fontsize=13, family="monospace")
fig.savefig(build.OUT / "concept_modules.png", dpi=105, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("wrote", build.OUT / "concept_modules.png")


# third sheet: the power pod and the LED strip from behind
fig = plt.figure(figsize=(15, 6.5), facecolor="#14141a")
px, py, zs, h = module.pose(power.POD_ANGLE)
for i, (title, el, az, span, show_cover) in enumerate([
    ("power pod at the back, balances the cup and phone", 24, -105, 130, True),
    ("LED strip in the channel (cover removed), fed from the pod in two halves", 55, -100, 215, False),
]):
    ax = fig.add_subplot(1, 2, i + 1, projection="3d", facecolor="#14141a")
    mannequin(ax)
    for k in [k for k in ("skin", "rail", "lip") if k in comps]:
        add(ax, comps[k], COLORS[k])
    add(ax, extras["strip"], COLORS["strip"])
    add(ax, extras["pod"], COLORS["module"]); add(ax, extras["lid"], "#d6bcfa")
    if show_cover:
        add(ax, extras["diffuser"], COLORS["diffuser"], 0.5)
    frame(ax, (px * 0.3, py * 0.5, -20) if i else (px, py, zs + 10), span, el, az, title)
flush()
fig.suptitle(f"festival-yoke power, size {build.SIZE}", color="#e8e8ee", fontsize=13, family="monospace")
fig.savefig(build.OUT / "concept_power.png", dpi=105, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("wrote", build.OUT / "concept_power.png")
