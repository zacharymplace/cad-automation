"""Build out/viewer.html: interactive 3D view of the design on an average-adult mannequin.
Run: uv run --no-project --with cadquery view.py   then serve out/ (python3 -m http.server -d out)"""
import json
from pathlib import Path

import cadquery as cq

import build
import module

OUT = Path(__file__).parent / "out"
W = build.W

meshes = []
comps = build.components()
for q, shp in build.parts().items():
    for comp, cshape in comps.items():
        piece = shp.intersect(cshape)
        if not piece.vals():
            continue
        verts, tris = piece.val().tessellate(0.5)
        meshes.append({
            "name": f"{comp}_{q}",
            "group": comp,
            "v": [round(c, 2) for p in verts for c in (p.x, p.y, p.z)],
            "i": [i for t in tris for i in t],
        })

verts, tris = module.cup_module().val().tessellate(0.5)
meshes.append({"name": "cup_module", "group": "module",
               "v": [round(c, 2) for p in verts for c in (p.x, p.y, p.z)], "i": [i for t in tris for i in t]})

mannequin = {  # average adult, mm, neck base (C7) at z=0, front is +y
    "head": {"c": [0, 6, 190], "r": [77, 98, 115]},
    "neck_r": 55,
    "shoulder": {"a": W["shoulder_half_width"] + 15, "b": W["shoulder_half_depth"] - 5, "drop": W["shoulder_drop"]},
}
cfg = {"neck_a": W["neck_opening_a"], "neck_b": W["neck_opening_b"], "head_circ": W["head_circumference"]}

html = (Path(__file__).parent / "viewer_template.html").read_text()
html = html.replace("/*DATA*/", f"const MESHES={json.dumps(meshes)};const MAN={json.dumps(mannequin)};")
(OUT / "viewer.html").write_text(html)
print("wrote", OUT / "viewer.html", f"({len(html)/1e6:.1f} MB)")
