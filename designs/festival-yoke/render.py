"""Static renders of the yoke on a mannequin -> out/<size>/preview.png and parts.png
Run: uv run --no-project --with cadquery --with matplotlib render.py"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import build
import module
from viz import COLORS, mannequin, shade, tris_of

fig = plt.figure(figsize=(16, 6.2), facecolor="#14141a")
views = [("3/4 front", 22, 62), ("side", 0, 0), ("top", 90, -90)]
comps = build.components()
comps["module"] = module.cup_module().union(module.phone_module()).union(module.dock_module()).union(module.fan_module())
comps["diffuser"] = build.diffuser()
for i, (title, el, az) in enumerate(views):
    ax = fig.add_subplot(1, 3, i + 1, projection="3d", facecolor="#14141a")
    mannequin(ax)
    for name, shp in comps.items():
        tr = tris_of(shp)
        ax.add_collection3d(Poly3DCollection(tr, facecolors=shade(tr, COLORS[name], 0.55 if name == "diffuser" else 1.0), edgecolor="none"))
    ax.set_xlim(-200, 200); ax.set_ylim(-200, 200); ax.set_zlim(-60, 340)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(el, az); ax.set_axis_off()
    ax.set_title(title, color="#e8e8ee", fontsize=11, family="monospace")
fig.suptitle("festival-yoke v1 size " + build.SIZE + "  |  orange skin (TPU)  teal module rail  yellow LED lip  purple modules  pale yellow LED cover  |  nothing above the shoulders", color="#e8e8ee", fontsize=11, family="monospace")
fig.savefig(build.OUT / "preview.png", dpi=110, facecolor=fig.get_facecolor(), bbox_inches="tight")

# print split, pulled apart so the dovetail joints show
fig = plt.figure(figsize=(14, 6.2), facecolor="#14141a")
PART_COLORS = {"fr": "#ff7a59", "br": "#2bb5a6", "fl": "#f2c230", "bl": "#9f7aea"}
for i, (title, el, az) in enumerate([("top, pulled apart", 90, -90), ("3/4 front, pulled apart", 30, 62)]):
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
