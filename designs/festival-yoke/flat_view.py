"""Plot the four flat skin patterns -> out/<size>/flat_patterns.png. Run: uv run --no-project --with cadquery --with matplotlib flat_view.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import build
import flatpack

fig, axes = plt.subplots(2, 2, figsize=(13, 11), facecolor="#14141a")
for ax, (name, (pat, body)) in zip(axes.ravel(), flatpack.flat_parts().items()):
    v, t = body.val().tessellate(0.1)
    p = np.array([[q.x, q.y, q.z] for q in v])
    tris = p[np.array(t)]
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    top = tris[n[:, 2] > 0.5 * np.linalg.norm(n, axis=1)]
    for tr in top:
        ax.fill(tr[:, 0], tr[:, 1], color="#ff7a59", linewidth=0.1, edgecolor="#ff7a59")
    z = np.array([tr[:, 2].mean() for tr in tris])
    groove = tris[(np.abs(n[:, 2]) > 0.5 * np.linalg.norm(n, axis=1)) & (z < flatpack.T - 0.05) & (z > 0.1) & (n[:, 2] > 0)]
    for tr in groove:
        ax.fill(tr[:, 0], tr[:, 1], color="#14141a", linewidth=0.1, edgecolor="#14141a", alpha=0.7)
    ax.set_aspect("equal"); ax.set_facecolor("#14141a"); ax.axis("off")
    bb = body.val().BoundingBox()
    ax.set_title(f"flat_{name}: {bb.xlen:.0f} x {bb.ylen:.0f} mm, {body.val().Volume() / 1000 * 1.25:.0f} g", color="#e8e8ee", family="monospace", fontsize=11)
fig.suptitle(f"flat TPU skin patterns, size {build.SIZE} (print face up; bend into the cone, join on the dovetails)", color="#e8e8ee", family="monospace")
fig.savefig(build.OUT / "flat_patterns.png", dpi=90, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("wrote", build.OUT / "flat_patterns.png")
