# Print plan: size XXL, kit full

Nothing here has been printed. This plan puts the cheap, informative tests first and holds back every big print until
the one before it has been checked. Part names match the files in `out/XXL/` (STL files are not committed:
run `build.py`, `module.py` and `power.py` to make them).

## Stages

**Stage 0: printer and material check (an afternoon).**
Print a 20 mm calibration cube in each filament, then a 2 mm thick, 60 x 40 mm TPU plate. The TPU plate must come out
smooth with no stringing or gaps: the yoke skin is that thin. Fix temperature, speed and retraction here, not on the yoke.

**Stage 1: the fit pack (the first real print, about 135 g).**
Print `flat_skin_fr` and `flat_skin_br` (TPU, flat, no supports), `hoop_lip_right` and `hoop_bar_coupon` (PETG, upside down), `diffuser_fitted_fr` (natural PETG) and `module_clip_coupon` (PETG). Together they test, with
no waste: forming the flat skin into the cone, the dovetail seam (the front-right tabs go into the back-right pockets), gluing a lip segment and a docking bar on along the engraved guide lines, the clip sliding onto the bar, the
diffuser snap, and how TPU behaves at 2 mm.

Check, and write the result down:
1. The two skin pieces bend into the cone and the dovetails push together and hold. If they are loose or will not close, change `joint.clearance` in `config.toml` by 0.1 mm and reprint only the pockets' piece.
2. The lip segment and the bar sit flat on the skin along the guide lines and bond: pull hard on the bar's flange in the direction a heavy module would lift it (the strength check flags the glue joint as the weak link). The clip then slides onto the bar from its open end with light force and the printed detent clicks into the dimples. If it binds, raise `CLEAR` in `module.py` or check the bar is straight; if it rocks, lower it.
3. The diffuser pushes onto the lip with a click and does not fall off when you shake it. If it is too tight or too loose, change `SNAP_DEPTH` or the bead steps in `build.py`.
4. Hold the formed pieces against a shoulder (see MEASURING.md): slope, opening and where the edge lands. The flat pattern is an exact unrolling of the formed shape, so a wrong slope means wrong measurements, not a wrong pattern.

Do not go further until 1 and 2 pass. The biggest unknown is whether a flat TPU sheet, glued to rigid segments, holds the cone shape well enough on the body: that is what this stage tells you.

**Stage 2: the whole bare collar (about 213 g of TPU, plus the rail and lip segments and the cover).**
Print the other two skin pieces, the remaining lip segments, the docking bars for the modules you want and the other three cover quarters. Form and join the four skin pieces, glue on the segments and bars, add stick-on foam at the engraved ovals, and wear it without modules for ten minutes.
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

## Part list for size XXL

Orientation and support area are computed from the geometry: the orientation with the least overhang steeper than 45 degrees, out of the six upright ones that have at least 300 mm2 of bed contact. Treat it as a first guess and look at it in the slicer.

**The yoke is now printed flat.** The collar skin is almost exactly a developable cone (Gaussian curvature about 1e-7 per mm2), so each quarter unrolls into a flat fan shape with under 0.2% stretch. Those four TPU pieces need no supports, and the lip segments and the docking bars are separate rigid parts printed upside down, also support-free. The formed shape (`yoke_*.stl` from `build.py`) is kept only as the reference for the clash and balance checks. The cover still needs light supports. Time is a rough guess from the mass (TPU 8 g/h, PETG 16 g/h).

| Part | Material | What | Best orientation | Support mm2 | Bed contact mm2 | Size mm | Fits bed | Mass g | Hours |
|---|---|---|---|---|---|---|---|---|---|
| `flat_skin_fr` | TPU 95A | flat skin quarter (print flat, bend into the cone) | as designed | 0 | 22469 | 206 x 192 x 2 | ok | 50 | 6.3 |
| `flat_skin_br` | TPU 95A | flat skin quarter (print flat, bend into the cone) | as designed | 0 | 25123 | 246 x 189 x 2 | NO | 56 | 7.0 |
| `flat_skin_fl` | TPU 95A | flat skin quarter (print flat, bend into the cone) | as designed | 0 | 22468 | 206 x 192 x 2 | ok | 50 | 6.3 |
| `flat_skin_bl` | TPU 95A | flat skin quarter (print flat, bend into the cone) | as designed | 0 | 24922 | 239 x 189 x 2 | NO | 56 | 7.0 |
| `hoop_lip_right_a` | PETG | lip segment, glued to the skin (print upside down) | flipped | 457 | 346 | 101 x 176 x 13 | ok | 4 | 0.2 |
| `hoop_lip_right_b` | PETG | lip segment, glued to the skin (print upside down) | as designed | 284 | 197 | 90 x 83 x 13 | ok | 2 | 0.1 |
| `hoop_lip_front_right` | PETG | lip segment, glued to the skin (print upside down) | as designed | 242 | 156 | 95 x 27 x 13 | ok | 2 | 0.1 |
| `hoop_lip_front_left` | PETG | lip segment, glued to the skin (print upside down) | as designed | 242 | 154 | 95 x 27 x 13 | ok | 2 | 0.1 |
| `hoop_lip_left_a` | PETG | lip segment, glued to the skin (print upside down) | flipped | 457 | 346 | 101 x 176 x 13 | ok | 4 | 0.2 |
| `hoop_lip_left_b` | PETG | lip segment, glued to the skin (print upside down) | as designed | 284 | 197 | 90 x 83 x 13 | ok | 2 | 0.1 |
| `hoop_lip_back_a` | PETG | lip segment, glued to the skin (print upside down) | on its +y side | 1371 | 422 | 163 x 13 x 29 | ok | 3 | 0.2 |
| `hoop_lip_back_b` | PETG | lip segment, glued to the skin (print upside down) | as designed | 247 | 157 | 97 x 27 x 13 | ok | 2 | 0.1 |
| `hoop_bar_cup` | PETG | docking bar, glued to the skin (print upside down) | as designed | 2894 | 0 | 80 x 75 x 25 | ok | 7 | 0.5 |
| `hoop_bar_phone` | PETG | docking bar, glued to the skin (print upside down) | as designed | 3040 | 0 | 85 x 63 x 27 | ok | 8 | 0.5 |
| `hoop_bar_dock` | PETG | docking bar, glued to the skin (print upside down) | as designed | 2928 | 0 | 82 x 71 x 26 | ok | 8 | 0.5 |
| `hoop_bar_fan` | PETG | docking bar, glued to the skin (print upside down) | as designed | 2928 | 0 | 82 x 71 x 26 | ok | 8 | 0.5 |
| `hoop_bar_pod` | PETG | docking bar, glued to the skin (print upside down) | as designed | 2961 | 0 | 80 x 30 x 28 | ok | 8 | 0.5 |
| `hoop_bar_id` | PETG | docking bar, glued to the skin (print upside down) | as designed | 2707 | 0 | 30 x 80 x 22 | ok | 7 | 0.5 |
| `hoop_bar_tube` | PETG | docking bar, glued to the skin (print upside down) | as designed | 2707 | 0 | 30 x 80 x 22 | ok | 7 | 0.5 |
| `diffuser_fitted_fr` | PETG (natural) | LED cover quarter | as designed | 7678 | 382 | 195 x 157 x 28 | ok | 13 | 0.9 |
| `diffuser_fitted_br` | PETG (natural) | LED cover quarter | as designed | 8001 | 421 | 230 x 159 x 28 | NO | 13 | 1.0 |
| `diffuser_fitted_fl` | PETG (natural) | LED cover quarter | as designed | 7559 | 373 | 195 x 157 x 28 | ok | 13 | 0.9 |
| `diffuser_fitted_bl` | PETG (natural) | LED cover quarter | as designed | 8000 | 429 | 230 x 159 x 28 | NO | 13 | 1.0 |
| `module_clip_coupon` | PETG | fit test for the clip's T-slot (slides onto the bar) | flipped | 602 | 657 | 52 x 47 x 15 | ok | 8 | 0.5 |
| `hoop_bar_coupon` | PETG | docking bar for the clip coupon | as designed | 2894 | 0 | 80 x 75 x 25 | ok | 7 | 0.5 |
| `module_cup` | PETG | cup cradle | as designed | 2141 | 3652 | 134 x 142 x 116 | ok | 42 | 2.6 |
| `module_phone` | PETG | phone cradle | as designed | 4105 | 1833 | 108 x 116 x 174 | ok | 41 | 2.6 |
| `module_dock` | PETG | ear-defender dock | on its +y side | 4661 | 355 | 128 x 35 x 145 | ok | 33 | 2.0 |
| `module_fan` | PETG | fan frame | as designed | 5886 | 582 | 114 x 112 x 113 | ok | 27 | 1.7 |
| `module_pod` | PETG | power pod tray | on its +x side | 1382 | 1071 | 29 x 49 x 71 | ok | 16 | 1.0 |
| `module_id` | PETG | ID card pouch | flipped | 953 | 2343 | 96 x 94 x 62 | ok | 23 | 1.4 |
| `module_tube` | PETG | hydration tube clip | as designed | 996 | 582 | 47 x 56 x 25 | ok | 8 | 0.5 |
| `module_fan_guard` | PETG | fan outlet guard (screws on with four M2 self-tapping screws) | as designed | 0 | 2941 | 86 x 86 x 2 | ok | 5 | 0.3 |
| `module_pod_lid` | PETG | power pod lid | flipped | 3 | 3054 | 71 x 48 x 28 | ok | 5 | 0.3 |

Printed mass without the coupon: about 538 g.

**Bed:** this size has 4 part(s) that do not fit the configured 220 x 220 mm bed: `flat_skin_br` (246 x 189), `flat_skin_bl` (239 x 189), `diffuser_fitted_br` (230 x 159), `diffuser_fitted_bl` (230 x 159). The largest part is 246 mm, so it needs a bed of about 249 mm, or change `bed` under `[print]` in `config.toml` to see the rest of the plan for your printer.

## Things this plan cannot tell you

- Whether the clearances (0.25 mm dovetail, 0.3 mm rail pocket, the 0.5 mm snap groove) suit your printer. That is what Stage 1 is for.
- Whether TPU at 2 mm prints reliably on your machine. Stage 0 is for that.
- How the collar feels on a body. Only Stage 2 tells you.
- Whether the electronics are safe. Stage 4 is a bench test, not a certification.
