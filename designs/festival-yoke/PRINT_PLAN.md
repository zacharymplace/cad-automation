# Print plan: size M, kit full

Nothing here has been printed. This plan puts the cheap, informative tests first and holds back every big print until
the one before it has been checked. Part names match the files in `out/M/` (STL files are not committed:
run `build.py`, `module.py` and `power.py` to make them).

## Stages

**Stage 0: printer and material check (an afternoon).**
Print a 20 mm calibration cube in each filament, then a 2 mm thick, 60 x 40 mm TPU plate. The TPU plate must come out
smooth with no stringing or gaps: the yoke skin is that thin. Fix temperature, speed and retraction here, not on the yoke.

**Stage 1: the fit pack (the first real print, about 88 g).**
Print `flat_skin_fr` and `flat_skin_br` (TPU, flat, no supports), `hoop_lip_right` and `hoop_bar_coupon` (PETG, upside down), `diffuser_fitted_fr` (natural PETG) and `module_clip_coupon` (PETG). Together they test, with
no waste: forming the flat skin into the cone, the dovetail seam (the front-right tabs go into the back-right pockets), gluing a lip segment and a docking bar on along the engraved guide lines, the clip sliding onto the bar, the
diffuser snap, and how TPU behaves at 2 mm.

Check, and write the result down:
1. The two skin pieces bend into the cone and the dovetails push together and hold. If they are loose or will not close, change `joint.clearance` in `config.toml` by 0.1 mm and reprint only the pockets' piece.
2. The lip segment and the bar sit flat on the skin along the guide lines and bond: pull hard on the bar's flange in the direction a heavy module would lift it (the strength check flags the glue joint as the weak link). The clip then slides onto the bar from its open end with light force and the printed detent clicks into the dimples. If it binds, raise `CLEAR` in `module.py` or check the bar is straight; if it rocks, lower it.
3. The diffuser pushes onto the lip with a click and does not fall off when you shake it. If it is too tight or too loose, change `SNAP_DEPTH` or the bead steps in `build.py`.
4. Hold the formed pieces against a shoulder (see MEASURING.md): slope, opening and where the edge lands. The flat pattern is an exact unrolling of the formed shape, so a wrong slope means wrong measurements, not a wrong pattern.

Do not go further until 1 and 2 pass. The biggest unknown is whether a flat TPU sheet, glued to rigid segments, holds the cone shape well enough on the body: that is what this stage tells you.

**Stage 2: the whole bare collar (about 120 g of TPU, plus the rail and lip segments and the cover).**
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

## Part list for size M

Orientation and support area are computed from the geometry: the orientation with the least overhang steeper than 45 degrees, out of the six upright ones that have at least 300 mm2 of bed contact. Treat it as a first guess and look at it in the slicer.

**The yoke is now printed flat.** The collar skin is almost exactly a developable cone (Gaussian curvature about 1e-7 per mm2), so each quarter unrolls into a flat fan shape with under 0.2% stretch. Those four TPU pieces need no supports, and the lip segments and the docking bars are separate rigid parts printed upside down, also support-free. The formed shape (`yoke_*.stl` from `build.py`) is kept only as the reference for the clash and balance checks. The cover still needs light supports. Time is a rough guess from the mass (TPU 8 g/h, PETG 16 g/h).

| Part | Material | What | Best orientation | Support mm2 | Bed contact mm2 | Size mm | Fits bed | Mass g | Hours |
|---|---|---|---|---|---|---|---|---|---|
| `flat_skin_fr` | TPU 95A | flat skin quarter (print flat, bend into the cone) | as designed | 0 | 12653 | 157 x 157 x 2 | ok | 28 | 3.5 |
| `flat_skin_br` | TPU 95A | flat skin quarter (print flat, bend into the cone) | as designed | 0 | 14214 | 200 x 155 x 2 | ok | 32 | 4.0 |
| `flat_skin_fl` | TPU 95A | flat skin quarter (print flat, bend into the cone) | as designed | 0 | 12652 | 157 x 157 x 2 | ok | 28 | 3.5 |
| `flat_skin_bl` | TPU 95A | flat skin quarter (print flat, bend into the cone) | as designed | 0 | 14014 | 190 x 155 x 2 | ok | 31 | 3.9 |
| `hoop_lip_right` | PETG | lip segment, glued to the skin (print upside down) | flipped | 580 | 441 | 81 x 212 x 13 | ok | 5 | 0.3 |
| `hoop_lip_front_right` | PETG | lip segment, glued to the skin (print upside down) | as designed | 186 | 117 | 71 x 22 x 13 | ok | 1 | 0.1 |
| `hoop_lip_front_left` | PETG | lip segment, glued to the skin (print upside down) | as designed | 186 | 116 | 71 x 22 x 13 | ok | 1 | 0.1 |
| `hoop_lip_left` | PETG | lip segment, glued to the skin (print upside down) | flipped | 579 | 441 | 81 x 212 x 13 | ok | 5 | 0.3 |
| `hoop_lip_back` | PETG | lip segment, glued to the skin (print upside down) | flipped | 453 | 344 | 212 x 24 x 13 | ok | 4 | 0.3 |
| `hoop_bar_cup` | PETG | docking bar, glued to the skin (print upside down) | as designed | 2948 | 0 | 80 x 75 x 27 | ok | 8 | 0.5 |
| `hoop_bar_phone` | PETG | docking bar, glued to the skin (print upside down) | as designed | 3086 | 0 | 85 x 63 x 29 | ok | 8 | 0.5 |
| `hoop_bar_dock` | PETG | docking bar, glued to the skin (print upside down) | as designed | 2980 | 0 | 82 x 72 x 28 | ok | 8 | 0.5 |
| `hoop_bar_fan` | PETG | docking bar, glued to the skin (print upside down) | as designed | 3021 | 0 | 82 x 72 x 28 | ok | 8 | 0.5 |
| `hoop_bar_pod` | PETG | docking bar, glued to the skin (print upside down) | as designed | 3090 | 0 | 80 x 30 x 31 | ok | 8 | 0.5 |
| `hoop_bar_id` | PETG | docking bar, glued to the skin (print upside down) | as designed | 2772 | 0 | 30 x 80 x 22 | ok | 7 | 0.5 |
| `hoop_bar_tube` | PETG | docking bar, glued to the skin (print upside down) | as designed | 2766 | 0 | 30 x 80 x 22 | ok | 7 | 0.5 |
| `diffuser_fitted_fr` | PETG (natural) | LED cover quarter | as designed | 3623 | 301 | 153 x 128 x 22 | ok | 7 | 0.5 |
| `diffuser_fitted_br` | PETG (natural) | LED cover quarter | as designed | 3567 | 344 | 188 x 130 x 22 | ok | 7 | 0.5 |
| `diffuser_fitted_fl` | PETG (natural) | LED cover quarter | as designed | 3468 | 296 | 153 x 128 x 22 | ok | 7 | 0.5 |
| `diffuser_fitted_bl` | PETG (natural) | LED cover quarter | as designed | 3552 | 350 | 188 x 130 x 22 | ok | 7 | 0.5 |
| `module_clip_coupon` | PETG | fit test for the clip's T-slot (slides onto the bar) | flipped | 602 | 657 | 51 x 47 x 15 | ok | 8 | 0.5 |
| `hoop_bar_coupon` | PETG | docking bar for the clip coupon | as designed | 2948 | 0 | 80 x 75 x 27 | ok | 8 | 0.5 |
| `module_cup` | PETG | cup cradle | as designed | 1917 | 3652 | 127 x 133 x 116 | ok | 41 | 2.5 |
| `module_phone` | PETG | phone cradle | as designed | 4027 | 1833 | 106 x 113 x 174 | ok | 41 | 2.6 |
| `module_dock` | PETG | ear-defender dock | on its +y side | 4618 | 382 | 128 x 35 x 145 | ok | 33 | 2.0 |
| `module_fan` | PETG | fan frame | as designed | 5886 | 582 | 114 x 112 x 113 | ok | 27 | 1.7 |
| `module_pod` | PETG | power pod tray | on its +x side | 1382 | 1071 | 29 x 49 x 71 | ok | 16 | 1.0 |
| `module_id` | PETG | ID card pouch | flipped | 953 | 2058 | 81 x 94 x 62 | ok | 21 | 1.3 |
| `module_tube` | PETG | hydration tube clip | as designed | 996 | 582 | 47 x 56 x 25 | ok | 8 | 0.5 |
| `module_fan_guard` | PETG | fan outlet guard (screws on with four M2 self-tapping screws) | as designed | 0 | 2941 | 86 x 86 x 2 | ok | 5 | 0.3 |
| `module_pod_lid` | PETG | power pod lid | flipped | 3 | 3054 | 71 x 48 x 28 | ok | 5 | 0.3 |

Printed mass without the coupon: about 416 g.

**Bed:** every part fits a 220 x 220 mm bed (the largest is 212 mm).

## Things this plan cannot tell you

- Whether the clearances (0.25 mm dovetail, 0.3 mm rail pocket, the 0.5 mm snap groove) suit your printer. That is what Stage 1 is for.
- Whether TPU at 2 mm prints reliably on your machine. Stage 0 is for that.
- How the collar feels on a body. Only Stage 2 tells you.
- Whether the electronics are safe. Stage 4 is a bench test, not a certification.
