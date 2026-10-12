"""Per-part print notes and PRINT_PLAN.md for the current size: material, best orientation by overhang, support area,
bed fit and rough time. Run: uv run --no-project --with cadquery print_plan.py"""
import math

import numpy as np

import build
import flatpack
import kit
import layout
import module
import power

ROT = {  # orientation name -> rotation matrix applied to the part as designed
    "as designed": np.eye(3),
    "flipped": np.diag([1, -1, -1]),
    "on its +x side": np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float),
    "on its -x side": np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float),
    "on its +y side": np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float),
    "on its -y side": np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float),
}
RATE = {"TPU 95A": 8.0, "PETG": 16.0, "PETG (natural)": 14.0}   # g/h, rough, thin walls and slow TPU


def tris(shape, tol=0.4):
    v, t = shape.val().tessellate(tol)
    p = np.array([[q.x, q.y, q.z] for q in v])
    return p[np.array(t)]


def analyse(shape):
    """Return {orientation: (overhang mm2, contact mm2, bbox dims)} for the six upright orientations."""
    base = tris(shape)
    out = {}
    for name, R in ROT.items():
        t = base @ R.T
        t[:, :, 2] -= t[:, :, 2].min()
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        area = np.linalg.norm(n, axis=1) / 2
        nz = n[:, 2] / (np.linalg.norm(n, axis=1) + 1e-12)
        low = t[:, :, 2].min(axis=1)
        over = float(area[(nz < -math.cos(math.radians(45))) & (low > 0.4)].sum())
        contact = float(area[(nz < -0.99) & (low <= 0.4)].sum())
        dims = t.reshape(-1, 3).max(axis=0) - t.reshape(-1, 3).min(axis=0)
        out[name] = (over, contact, tuple(float(d) for d in dims))
    return out


def parts():
    p = {}
    for q, (pat, body) in flatpack.flat_parts().items():
        p[f"flat_skin_{q}"] = (body, "TPU 95A", 0.9, "flat skin quarter (print flat, bend into the cone)")
    for name, seg in flatpack.hoop_segments().items():
        kind = "rail" if name.startswith("rail") else "lip"
        p[f"hoop_{name}"] = (seg, "PETG", 0.9, f"{kind} segment, glued to the skin (print upside down)")
    if layout.has_leds():
        dif = power.fitted_diffuser()
        for q, (sx, sy) in build.QUARTERS.items():
            p[f"diffuser_fitted_{q}"] = (build.quarter(dif, sx, sy), "PETG (natural)", 0.9, "LED cover quarter")
    p["module_clip_coupon"] = (module.clip_coupon(), "PETG", 0.7, "fit test for the rail clip")
    notes = {"cup": "cup cradle", "phone": "phone cradle", "dock": "ear-defender dock", "fan": "fan frame", "pod": "power pod tray",
             "id": "ID card pouch", "tube": "hydration tube clip", "blank": "blank mounting plate", "cover": "rail cover"}
    for name, shape in kit.modules().items():
        p[f"module_{name}"] = (shape, "PETG", 0.5, notes[name])
    if layout.has_leds():
        p["module_pod_lid"] = (power.pod_lid(), "PETG", 0.5, "power pod lid")
    return p


def main():
    bed = build.P["bed"]
    rows = []
    for name, (shape, mat, fill, note) in parts().items():
        res = analyse(shape)
        stable = {k: v for k, v in res.items() if v[1] >= 300}      # needs real bed contact, or it is balanced on an edge
        best = min(stable, key=lambda k: stable[k][0]) if stable else "as designed"
        over, contact, dims = res[best]
        fits = sorted(dims[:2]) <= sorted(bed[:2]) and dims[2] <= bed[2]
        grams = shape.val().Volume() / 1000 * build.P["density_g_cc"] * fill
        hours = grams / RATE[mat]
        rows.append((name, mat, note, best, over, contact, dims, fits, grams, hours))
    print(f"{'part':<22}{'material':<16}{'orientation':<16}{'support mm2':>12}{'bed':>5}{'g':>6}{'~h':>6}")
    for r in rows:
        print(f"{r[0]:<22}{r[1]:<16}{r[3]:<16}{r[4]:>12.0f}{'ok' if r[7] else 'NO':>5}{r[8]:>6.0f}{r[9]:>6.1f}")
    write_md(rows)


def write_md(rows):
    table = "\n".join(
        f"| `{n}` | {mat} | {note} | {best} | {over:.0f} | {contact:.0f} | {dims[0]:.0f} x {dims[1]:.0f} x {dims[2]:.0f} | {'ok' if fits else 'NO'} | {g:.0f} | {h:.1f} |"
        for n, mat, note, best, over, contact, dims, fits, g, h in rows
    )
    total_g = sum(r[8] for r in rows if not r[0].endswith("coupon"))
    md = f"""# Print plan: size {build.SIZE}, kit {layout.KIT}

Nothing here has been printed. This plan puts the cheap, informative tests first and holds back every big print until
the one before it has been checked. Part names match the files in `out/{build.SIZE}/` (STL files are not committed:
run `build.py`, `module.py` and `power.py` to make them).

## Stages

**Stage 0: printer and material check (an afternoon).**
Print a 20 mm calibration cube in each filament, then a 2 mm thick, 60 x 40 mm TPU plate. The TPU plate must come out
smooth with no stringing or gaps: the yoke skin is that thin. Fix temperature, speed and retraction here, not on the yoke.

**Stage 1: the fit pack (the first real print, about {sum(r[8] for r in rows if r[0] in ('flat_skin_fr', 'flat_skin_br', 'hoop_rail_right', 'hoop_lip_right', 'diffuser_fitted_fr', 'module_clip_coupon')):.0f} g).**
Print `flat_skin_fr` and `flat_skin_br` (TPU, flat, no supports), `hoop_rail_right` and `hoop_lip_right` (PETG, upside down), `diffuser_fitted_fr` (natural PETG) and `module_clip_coupon` (PETG). Together they test, with
no waste: forming the flat skin into the cone, the dovetail seam (the front-right tabs go into the back-right pockets), gluing a rail and lip on along the engraved guide lines, the rail clip and its screw holes, the
diffuser snap, and how TPU behaves at 2 mm.

Check, and write the result down:
1. The two skin pieces bend into the cone and the dovetails push together and hold. If they are loose or will not close, change `joint.clearance` in `config.toml` by 0.1 mm and reprint only the pockets' piece.
2. The rail and lip segments sit flat on the skin along the guide lines and bond. The clip then snaps onto the rail and the two M3 screws bite the stem. If it will not go on, raise `CLEAR` in `module.py`; if it rocks, lower it.
3. The diffuser pushes onto the lip with a click and does not fall off when you shake it. If it is too tight or too loose, change `SNAP_DEPTH` or the bead steps in `build.py`.
4. Hold the formed pieces against a shoulder (see MEASURING.md): slope, opening and where the edge lands. The flat pattern is an exact unrolling of the formed shape, so a wrong slope means wrong measurements, not a wrong pattern.

Do not go further until 1 and 2 pass. The biggest unknown is whether a flat TPU sheet, glued to rigid segments, holds the cone shape well enough on the body: that is what this stage tells you.

**Stage 2: the whole bare collar (about {sum(r[8] for r in rows if r[0].startswith('flat_skin')):.0f} g of TPU, plus the rail and lip segments and the cover).**
Print the other two skin pieces, the remaining rail and lip segments and the other three cover quarters. Form and join the four skin pieces, glue on the segments, add stick-on foam at the engraved ovals, and wear it without modules for ten minutes.
Gate: it sits on the shoulders without sliding or pressing on the neck, the front opening lets the head through, and nothing reaches above the shoulder line. If not, change the five measurements or `shoulder_drop` and rerun `build_all.py` and `flatpack.py`.

**Stage 3: modules, one at a time, under load.**
Print and test in this order, lightest consequences first:
1. `module_dock` with your real ear defenders (set `DOCK_CUP` to their size first).
2. `module_cup` with a 250 ml cup of water, then a full one. Hang it for an hour; look for creep at the clip.
3. `module_phone` with a dummy weight the size of your phone.
4. `module_fan` with the fan on a bench lead.
5. `module_pod` and lid, with a block of the right size and weight instead of a cell.
Watch each clip for cracks at the lips: they are 1.7 mm thick.

**Stage 4: electronics, off the body.**
Only after everything above fits. Wire the board, cell and strip on a bench first, in a fire-safe container, with a fuse or the board's own protection, and run for an hour watching temperature. Never charge a cell inside the collar, and never wear a cell you have not run on the bench.

## Slicer settings (starting points, not tuned)

| | TPU 95A (yoke) | PETG (modules, pod) | Natural PETG (cover) |
|---|---|---|---|
| Nozzle / layer | 0.4 mm / 0.2 mm | 0.4 mm / 0.2 mm | 0.4 mm / 0.2 mm |
| Temperature | 225-235 C, bed 50 C | 235-245 C, bed 80 C | 235-245 C, bed 80 C |
| Walls | 5 (the 2 mm skin should be walls only) | 3 | 3 (1.2 mm skin is walls only) |
| Infill | none needed on the skin; 100% for the pad seats | 20% gyroid | 100% (thin parts) |
| Speed | 20-30 mm/s, direct drive | 40-60 mm/s | 40 mm/s |
| Retraction | minimal (about 1 mm) | normal | normal |
| Cooling | 50-100% | 50-100% | 100% |
| Supports | none (flat) | only where the part table shows support area | tree supports under the slope, 0.2 mm top gap |
| Adhesion | PEI, glue stick as a release | PEI | PEI |

Print orientation matters for the clips: the lips load by bending along the layers when printed lying as designed, which is the strong direction. Do not stand a clip on its end.

## Part list for size {build.SIZE}

Orientation and support area are computed from the geometry: the orientation with the least overhang steeper than 45 degrees, out of the six upright ones that have at least 300 mm2 of bed contact. Treat it as a first guess and look at it in the slicer.

**The yoke is now printed flat.** The collar skin is almost exactly a developable cone (Gaussian curvature about 1e-7 per mm2), so each quarter unrolls into a flat fan shape with under 0.2% stretch. Those four TPU pieces need no supports, and the rail and lip are separate segments printed upside down, also support-free. The formed shape (`yoke_*.stl` from `build.py`) is kept only as the reference for the clash and balance checks. The cover still needs light supports. Time is a rough guess from the mass (TPU {RATE['TPU 95A']:.0f} g/h, PETG {RATE['PETG']:.0f} g/h).

| Part | Material | What | Best orientation | Support mm2 | Bed contact mm2 | Size mm | Fits bed | Mass g | Hours |
|---|---|---|---|---|---|---|---|---|---|
{table}

Printed mass without the coupon: about {total_g:.0f} g.

## Things this plan cannot tell you

- Whether the clearances (0.25 mm dovetail, 0.3 mm rail pocket, the 0.5 mm snap groove) suit your printer. That is what Stage 1 is for.
- Whether TPU at 2 mm prints reliably on your machine. Stage 0 is for that.
- How the collar feels on a body. Only Stage 2 tells you.
- Whether the electronics are safe. Stage 4 is a bench test, not a certification.
"""
    (build.ROOT / "PRINT_PLAN.md").write_text(md)
    print("wrote", build.ROOT / "PRINT_PLAN.md")


if __name__ == "__main__":
    main()
