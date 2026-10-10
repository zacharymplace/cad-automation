# Print plan: size M

Nothing here has been printed. This plan puts the cheap, informative tests first and holds back every big print until
the one before it has been checked. Part names match the files in `out/M/` (STL files are not committed:
run `build.py`, `module.py` and `power.py` to make them).

## Stages

**Stage 0: printer and material check (an afternoon).**
Print a 20 mm calibration cube in each filament, then a 2 mm thick, 60 x 40 mm TPU plate. The TPU plate must come out
smooth with no stringing or gaps: the yoke skin is that thin. Fix temperature, speed and retraction here, not on the yoke.

**Stage 1: the fit pack (the first real print, about 82 g).**
Print `yoke_fr` and `yoke_br` (rigid PETG proxy first, then TPU), `diffuser_fitted_fr` (natural PETG) and `module_clip_coupon` (PETG). Together they test, with
no waste: the dovetail seam (the front-right tabs go into the back-right pockets), the rail clip and its screw holes, the
diffuser snap, the edge rounding, and how TPU behaves at 2 mm.

Check, and write the result down:
1. The two yoke quarters push together and hold. If they are loose or will not close, change `joint.clearance` in `config.toml` by 0.1 mm and reprint only the pockets' quarter.
2. The clip snaps onto the rail and the two M3 screws bite the stem. If it will not go on, raise `CLEAR` in `module.py`; if it rocks, lower it.
3. The diffuser pushes onto the lip with a click and does not fall off when you shake it. If it is too tight or too loose, change `SNAP_DEPTH` or the bead steps in `build.py`.
4. Hold the two quarters against a shoulder (see MEASURING.md): slope, opening and where the edge lands.

Do not go further until 1 and 2 pass.

**Stage 2: the whole bare collar (about 131 g of TPU, plus the cover).**
Print the other two yoke quarters and the other three cover quarters. Join the four yoke quarters, add stick-on foam to the four pad seats, and wear it without modules for ten minutes.
Gate: it sits on the shoulders without sliding or pressing on the neck, the front opening lets the head through, and nothing reaches above the shoulder line. If not, change the five measurements or `shoulder_drop` and rerun `build_all.py`.

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
| Supports | yes, under the whole slope (see below) | where the part table shows support area | tree supports under the slope, 0.2 mm top gap |
| Adhesion | PEI, glue stick as a release | PEI | PEI |

Print orientation matters for the clips: the lips load by bending along the layers when printed lying as designed, which is the strong direction. Do not stand a clip on its end.

## Part list for size M

Orientation and support area are computed from the geometry: the orientation with the least overhang steeper than 45 degrees, out of the six upright ones that have at least 300 mm2 of bed contact. Treat it as a first guess and look at it in the slicer.

**The yoke quarters are the hard print.** The collar is a thin 23-42 degree cone, so most of its underside is an overhang and the part touches the bed on only a thin rim. Expect supports under the whole slope (several thousand mm2 per quarter, see the table), and a brim. Supports in TPU are fiddly. That is why Stage 1 prints the yoke quarters first in rigid PETG as a proxy: it checks the shape, the slope, the dovetails and the rail at far less risk, and it tells you how much support the slope really needs. Print the TPU versions only when the PETG ones fit. Rigid parts will be tighter at the joints than TPU, so judge clearances again on the TPU parts. Time is a rough guess from the mass (TPU 8 g/h, PETG 16 g/h).

| Part | Material | What | Best orientation | Support mm2 | Bed contact mm2 | Size mm | Fits bed | Mass g | Hours |
|---|---|---|---|---|---|---|---|---|---|
| `yoke_fr` | TPU 95A | yoke quarter | as designed | 8698 | 255 | 153 x 139 x 37 | ok | 31 | 3.9 |
| `yoke_br` | TPU 95A | yoke quarter | as designed | 9693 | 276 | 200 x 129 x 37 | ok | 34 | 4.3 |
| `yoke_fl` | TPU 95A | yoke quarter | as designed | 8657 | 256 | 153 x 139 x 37 | ok | 31 | 3.9 |
| `yoke_bl` | TPU 95A | yoke quarter | as designed | 9404 | 277 | 188 x 129 x 37 | ok | 34 | 4.2 |
| `diffuser_fitted_fr` | PETG (natural) | LED cover quarter | as designed | 3616 | 301 | 153 x 128 x 20 | ok | 7 | 0.5 |
| `diffuser_fitted_br` | PETG (natural) | LED cover quarter | as designed | 3343 | 345 | 188 x 130 x 20 | ok | 6 | 0.5 |
| `diffuser_fitted_fl` | PETG (natural) | LED cover quarter | as designed | 3613 | 296 | 153 x 128 x 20 | ok | 7 | 0.5 |
| `diffuser_fitted_bl` | PETG (natural) | LED cover quarter | as designed | 4177 | 350 | 188 x 130 x 20 | ok | 8 | 0.5 |
| `module_clip_coupon` | PETG | fit test for the rail clip | flipped | 382 | 880 | 51 x 47 x 14 | ok | 10 | 0.6 |
| `module_cup` | PETG | cup cradle | as designed | 1813 | 3652 | 124 x 130 x 113 | ok | 39 | 2.5 |
| `module_phone` | PETG | phone cradle | as designed | 4022 | 1833 | 113 x 115 x 174 | ok | 42 | 2.6 |
| `module_dock` | PETG | ear-defender dock | on its +y side | 4366 | 335 | 128 x 34 x 145 | ok | 32 | 2.0 |
| `module_fan` | PETG | fan frame | as designed | 5212 | 539 | 101 x 107 x 112 | ok | 28 | 1.7 |
| `module_pod` | PETG | power pod tray | flipped | 2920 | 666 | 84 x 72 x 29 | ok | 16 | 1.0 |
| `module_pod_lid` | PETG | power pod lid | flipped | 0 | 3277 | 84 x 72 x 4 | ok | 5 | 0.3 |

Printed mass without the coupon: about 321 g.

## Things this plan cannot tell you

- Whether the clearances (0.25 mm dovetail, 0.3 mm rail pocket, the 0.5 mm snap groove) suit your printer. That is what Stage 1 is for.
- Whether TPU at 2 mm prints reliably on your machine. Stage 0 is for that.
- How the collar feels on a body. Only Stage 2 tells you.
- Whether the electronics are safe. Stage 4 is a bench test, not a certification.
