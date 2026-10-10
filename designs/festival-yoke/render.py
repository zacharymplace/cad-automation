"""Static renders of the yoke on a mannequin -> out/preview.png
Run: uv run --no-project --with cadquery --with matplotlib render.py"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import build
import module
import sizing

COLORS = {"skin": "#ff7a59", "rail": "#2bb5a6", "lip": "#f2c230", "module": "#b794f4"}
LIGHT = np.array([0.4, -0.5, 0.8]); LIGHT /= np.linalg.norm(LIGHT)


def tris_of(shape, tol=0.5):
    v, t = shape.val().tessellate(tol)
    p = np.array([[x.x, x.y, x.z] for x in v])
    return p[np.array(t)]


def shade(tris, color, alpha=1.0):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    k = 0.45 + 0.55 * np.abs(n @ LIGHT)
    return [(*(np.array(to_rgb(color)) * kk), alpha) for kk in k]


def mannequin(ax):
    hp, hq = sizing.head_axes(build.W["head_circumference"])
    neck_r = build.W["neck_circumference"] / (2 * np.pi)
    u, v = np.mgrid[0:2 * np.pi:40j, 0:np.pi:24j]
    ax.plot_surface(hp * np.cos(u) * np.sin(v), 6 + hq * np.sin(u) * np.sin(v), 190 + 115 * hq / 98 * np.cos(v), color="#9aa0b4", alpha=0.35, linewidth=0)
    z = np.linspace(-60, 90, 2); th = np.linspace(0, 2 * np.pi, 40)
    T, Z = np.meshgrid(th, z)
    ax.plot_surface(neck_r * np.cos(T), neck_r * np.sin(T), Z, color="#9aa0b4", alpha=0.35, linewidth=0)
    th = np.linspace(0, 2 * np.pi, 60); z = np.linspace(-45, -200, 2)
    T, Z = np.meshgrid(th, z)
    ax.plot_surface((build.AO - 5) * np.cos(T), (build.BO - 10) * np.sin(T), Z, color="#9aa0b4", alpha=0.3, linewidth=0)


fig = plt.figure(figsize=(16, 6.2), facecolor="#14141a")
views = [("3/4 front", 22, -55), ("side", 0, 0), ("top", 90, -90)]
comps = build.components()
comps["module"] = module.cup_module()
for i, (title, el, az) in enumerate(views):
    ax = fig.add_subplot(1, 3, i + 1, projection="3d", facecolor="#14141a")
    mannequin(ax)
    for name, shp in comps.items():
        tr = tris_of(shp)
        ax.add_collection3d(Poly3DCollection(tr, facecolors=shade(tr, COLORS[name]), edgecolor="none"))
    ax.set_xlim(-200, 200); ax.set_ylim(-200, 200); ax.set_zlim(-60, 340)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(el, az); ax.set_axis_off()
    ax.set_title(title, color="#e8e8ee", fontsize=11, family="monospace")
fig.suptitle("festival-yoke v1 size " + build.SIZE + "  |  orange skin (TPU)  teal module rail  yellow LED lip  purple cup module  |  nothing above the shoulders", color="#e8e8ee", fontsize=11, family="monospace")
fig.savefig(build.OUT / "preview.png", dpi=110, facecolor=fig.get_facecolor(), bbox_inches="tight")

# print split, pulled apart so the dovetail joints show
fig = plt.figure(figsize=(14, 6.2), facecolor="#14141a")
PART_COLORS = {"fr": "#ff7a59", "br": "#2bb5a6", "fl": "#f2c230", "bl": "#9f7aea"}
for i, (title, el, az) in enumerate([("top, pulled apart", 90, -90), ("3/4, pulled apart", 30, -50)]):
    ax = fig.add_subplot(1, 2, i + 1, projection="3d", facecolor="#14141a")
    for name, shp in build.parts().items():
        sx, sy = build.QUARTERS[name]
        tr = tris_of(shp) + np.array([sx * 22, sy * 22, 0])
        ax.add_collection3d(Poly3DCollection(tr, facecolors=shade(tr, PART_COLORS[name]), edgecolor="none"))
    ax.set_xlim(-220, 220); ax.set_ylim(-220, 220); ax.set_zlim(-120, 120)
    ax.set_box_aspect((1, 1, 0.5)); ax.view_init(el, az); ax.set_axis_off()
    ax.set_title(title, color="#e8e8ee", fontsize=11, family="monospace")
fig.suptitle("festival-yoke v1 size " + build.SIZE + "  |  four print parts, dovetail tabs and pockets (0.25 mm clearance)", color="#e8e8ee", fontsize=11, family="monospace")
fig.savefig(build.OUT / "parts.png", dpi=110, facecolor=fig.get_facecolor(), bbox_inches="tight")
