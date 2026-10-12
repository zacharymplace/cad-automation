"""One image of the active kit on the mannequin -> out/<size>/kit_<kit>.png, then `kits.png` montage when run with --montage.
Run per kit: FESTIVAL_YOKE_KIT=glow uv run --no-project --with cadquery --with matplotlib concept_kit.py
"""
import sys

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import build
import layout
from viz import COLORS, mannequin, shade, tris_of


def render():
    import balance
    import kit
    import power

    comps = build.components()
    comps["pad"] = build.pads()   # drawn for the underside view only; the real seats are foam stickers
    items = []

    def add(shape, color, alpha=1.0):
        tr = tris_of(shape)
        items.append((tr, shade(tr, color, alpha)))

    fig = plt.figure(figsize=(7.5, 6.5), facecolor="#14141a")
    ax = fig.add_subplot(1, 1, 1, projection="3d", facecolor="#14141a")
    mannequin(ax)
    for k in [k for k in ("skin", "rail", "lip", "pad") if k in comps]:
        add(comps[k], COLORS[k])
    for shape in kit.modules().values():
        add(shape, COLORS["module"])
    if layout.has_leds():
        add(power.strip(), COLORS["strip"])
        add(power.fitted_diffuser(), COLORS["diffuser"], 0.5)
    tr = np.concatenate([t for t, _ in items])
    fc = [c for _, cs in items for c in cs]
    ax.add_collection3d(Poly3DCollection(tr, facecolors=fc, edgecolor="none"))
    ax.set_xlim(-250, 250); ax.set_ylim(-250, 250); ax.set_zlim(-120, 380)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(24, 78); ax.set_axis_off()
    s = balance.summary(layout.angles(), balance.setup())
    mods = ", ".join(layout.present()) or "no modules"
    ax.set_title(f"{layout.KIT}: {mods}\nprinted {s['printed']} g  |  loaded {s['full']['mass']} g, centre {s['full']['offset']:.0f} mm off, {s['full']['margin']:.0f} mm margin",
                 color="#e8e8ee", fontsize=10, family="monospace")
    fig.savefig(build.OUT / f"kit_{layout.KIT}.png", dpi=100, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print("wrote", build.OUT / f"kit_{layout.KIT}.png")


def montage():
    import matplotlib.image as mpimg
    names = list(layout.KITS)
    fig, axes = plt.subplots(2, 3, figsize=(18, 11), facecolor="#14141a")
    for ax in axes.ravel():
        ax.axis("off")
    for ax, name in zip(axes.ravel(), names):
        ax.imshow(mpimg.imread(build.OUT / f"kit_{name}.png"))
    fig.suptitle(f"festival-yoke kits, size {build.SIZE}", color="#e8e8ee", fontsize=14, family="monospace")
    fig.savefig(build.OUT / "kits.png", dpi=90, facecolor=fig.get_facecolor(), bbox_inches="tight")
    print("wrote", build.OUT / "kits.png")


if __name__ == "__main__":
    montage() if "--montage" in sys.argv else render()
