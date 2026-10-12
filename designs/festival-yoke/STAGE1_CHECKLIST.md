# Stage 1 checklist: the fit pack (size M)

Print this and tick it off. It covers Stage 0 (printer check) and Stage 1 (the fit pack) of `PRINT_PLAN.md`. Nothing here involves a battery, and nothing is worn. About 88 g of filament and 9-10 hours of printing, most of it the two TPU pieces.

**What Stage 1 answers**
1. Does a flat TPU sheet bend into the collar cone and hold it, once rigid parts are glued on?
2. Do the dovetails join the pieces?
3. Does the bar's glue joint survive a pull?
4. Does the clip slide onto the bar with a light push?
5. Does the cover snap onto the lip?

If 1 or 3 fails, stop and tell me before printing more.

---

## 0. Before you print

- [ ] Printer prints TPU 95A without jamming (direct drive helps) and PETG, and has a bed of at least 220 x 220 mm.
- [ ] 1 kg TPU 95A, 1 kg PETG, and a small amount of natural (clear) PETG.
- [ ] Flexible adhesive for PETG to TPU (flexible cyanoacrylate or an MS polymer), isopropyl alcohol, 400-grit sandpaper, nitrile gloves, eye protection.
- [ ] Digital calipers, a spring scale reading to at least 10 kg (about 100 N), a flat piece of glass or a steel rule, a feeler gauge or paper strips (0.1-0.3 mm).
- [ ] An M3 spring plunger (ball tip, stainless, about 6 mm long). The test works without it, but you will not feel the detent.
- [ ] Make a fresh set of STL files (the old `out/M/` folder still holds files from earlier designs, such as `hoop_rail_*.stl` and `yoke_*.stl`: **do not print those**). Run these three, one at a time, from the project folder:

```bash
uv run --no-project --with cadquery python flatpack.py
```

```bash
uv run --no-project --with cadquery python module.py
```

```bash
uv run --no-project --with cadquery python power.py
```

- [ ] The files you need now exist in `out/M/`: `flat_skin_fr.stl`, `flat_skin_br.stl`, `hoop_lip_right.stl`, `hoop_bar_cup.stl`, `module_clip_coupon.stl`, `diffuser_fitted_fr.stl`.

## 1. Stage 0: printer and material check (an afternoon)

- [ ] Print a 20 mm cube in TPU and one in PETG. Measure each side with the calipers and note it: ______ / ______ mm (want 20.0 within 0.2).
- [ ] Print a 2 mm thick, 60 x 40 mm TPU plate, flat, no supports. It must come out smooth: no stringing, no gaps between lines, no curling at the corners.
- [ ] Bend the TPU plate to a curve of about 100 mm radius by hand. It should spring back without whitening or cracking.
- [ ] Settings that worked (write them down): TPU temp ____ C, speed ____ mm/s, retraction ____ mm; PETG temp ____ C, bed ____ C.

If the TPU plate is not clean, fix it here. The skin is that thin.

## 2. The prints

Use the slicer table in `PRINT_PLAN.md` as a starting point. Look at every part in the slicer before you start; the orientations below come from the geometry, but you should see them.

| # | File | Material | Orientation | Supports | Mass | Time | Done |
|---|---|---|---|---|---|---|---|
| 1 | `flat_skin_fr.stl` | TPU 95A | flat, face up | none | 28 g | 3.5 h | [ ] |
| 2 | `flat_skin_br.stl` | TPU 95A | flat, face up | none | 31 g | 3.9 h | [ ] |
| 3 | `hoop_lip_right.stl` | PETG | upside down (lip top on the bed) | only where the slicer shows the groove overhang | 5 g | 0.3 h | [ ] |
| 4 | `hoop_bar_cup.stl` | PETG | upside down (cap on the bed) | none | 6 g | 0.4 h | [ ] |
| 5 | `module_clip_coupon.stl` | PETG | flat, as the slicer drops it | none or light | 10 g | 0.6 h | [ ] |
| 6 | `diffuser_fitted_fr.stl` | natural PETG | as designed | light tree supports, 0.2 mm top gap | 7 g | 0.5 h | [ ] |

Print settings: TPU 5 walls, no infill needed (the 2 mm skin is walls only), 20-30 mm/s. PETG parts 3 walls, 20% gyroid. Cover 100% infill, 100% cooling.

Print order: PETG parts first (3-6), so you can test the bar and clip while the TPU prints.

After each print:
- [ ] Weigh it and note the mass: skin fr ____ g, skin br ____ g, lip ____ g, bar ____ g, clip ____ g, cover ____ g.
- [ ] Look for warping. A TPU piece must lie flat on a table; a PETG part must not bow.
- [ ] Deburr every edge a hand will touch.

## 3. Checks before gluing

**Bar straightness** (it must stay straight or the clip binds)
- [ ] Lay `hoop_bar_cup` on glass or a steel rule with the flat cap face down. Slide a 0.3 mm feeler under it anywhere along its 80 mm length: it must not fit. Gap measured: ______ mm.

**Clip on bar (before any glue)**
- [ ] Slide the clip coupon onto the bar from the open end (the end without the stop block). Push force by hand or scale: ______ N (want under 15 N, about 1.5 kg).
- [ ] It slides the whole travel (about 12 mm each way) without binding.
- [ ] It cannot be lifted straight up off the bar (the T-slot holds it). It comes off only by sliding out the open end.
- [ ] Rocking: hold the bar and wiggle the clip. Play side to side: ______ mm (want under 0.6 mm in total).
- [ ] If you fitted the spring plunger: it clicks into one of the three dimples (centre and 10 mm either side).

**Dovetail on the skin (flat, before forming)**
- [ ] The two tabs on `flat_skin_fr` fit the two pockets on `flat_skin_br` when you lay the edges together. Measure a tab at its widest: ______ mm and its pocket: ______ mm (want about 0.5 mm of play).

If the clip binds, raise `CLEAR` in `module.py` from 0.3 to 0.4; if it rocks, lower it to 0.2.

## 4. Forming and joining

- [ ] Bend `flat_skin_fr` into a cone: its two straight edges and its curved edges follow the shape in `out/M/flat_patterns.png`. It must bend without kinking or whitening.
- [ ] Bend `flat_skin_br` the same way and slide the tabs into the pockets along the shared seam (the seam is 97 mm long).
- [ ] The joint closes and holds: pull gently across the seam with both hands. Note how it holds: ______.
- [ ] The two pieces together make a quarter-ring that sits in the cone shape when you rest it on a table or against your shoulder.

If the dovetails are too loose or will not close, change `joint.clearance` in `config.toml` by 0.1 mm, rerun `flatpack.py`, and reprint only the piece whose pockets are wrong.

## 5. Gluing the lip and bar

Do this in a ventilated place with gloves and eye protection. Cyanoacrylate bonds skin in seconds.

- [ ] Scuff the base of the lip segment and the bar with 400-grit and wipe with isopropyl alcohol. Wipe the matching places on the TPU too.
- [ ] Find the engraved guide lines on the skin: the long arc is the lip; the straight line near 40 degrees on `flat_skin_fr` is the bar's centre line.
- [ ] Glue the lip segment along its guide line, straddling the seam between the two skin pieces, with the groove facing outward. Hold or clamp it flat.
- [ ] Find the two small holes under the bar's guide line (they are for the bar's pegs). Push the bar's two barbed pegs through them from the outside; each barb should snap through and sit under the skin. Push-through force: ______ N (it should need a firm push, not a tool). Note if the TPU tears or the barb will not pass.
- [ ] Glue the bar on its centre line, flange down, with the **stop-block end toward the front gap** (the higher-angle end, as in the viewer); for this test either way round works, but keep the open end clear so the clip can slide on. Check by sliding the clip on afterward.
- [ ] Wait the full cure time on the adhesive, at least 24 hours before the pull test.

## 6. After the glue has cured

**Bar pull test** (this is the weakest joint in the design; the bar has a 30 mm glued flange and two barbed pegs through the skin)
- [ ] Put the clip on the bar and hook the spring scale to it.
- [ ] Pull **straight up** on the clip. The numbers are what a heavy module can do to the glue:
  - 18 N (about 1.8 kg): a full cup standing still. Hold 10 s. Result: [ ] holds [ ] fails
  - 90 N (about 9 kg): a 5 g bump on that cup. Hold 10 s. Result: [ ] holds [ ] fails
- [ ] Record where it failed if it did: [ ] glue let go from TPU [ ] glue let go from PETG [ ] TPU tore [ ] bar cracked [ ] a barb pulled back through its hole.
- [ ] Measure the pegs on their own: before gluing a spare bar, hook the scale to the bar and pull straight up until the pegs let go. Pull-out force: ______ N for the pair (I assumed 30 N). And measure the glue alone by pulling a glued flange with the pegs cut off: ______ N.

If it fails below 90 N: tell me what let go. The next step is a screw through the bar and skin into a small backing plate, which does not depend on the glue.

**Lip and cover**
- [ ] Press `diffuser_fitted_fr` onto the lip over the part of the ring where the lip segment is glued (0 to 45 degrees). It pushes on with a click and does not fall off when you shake it.
- [ ] Pull-off force: ______ N (a few newtons is right; it should not drop off by itself, and you should be able to remove it).
- [ ] If it is too tight or too loose, change `SNAP_DEPTH` or the bead steps (`BEAD_LEAD`, `BEAD_STEP`) in `build.py` and reprint only the cover.

**Does the cone hold itself?**
- [ ] Put the assembled piece down on a flat surface. Does it keep the cone shape, or sag flat? Note: ______.
- [ ] Hold it against your shoulder following the size M numbers in `MEASURING.md` (shoulder width 380 mm, shoulder drop 40 mm). Is the slope right? Does the edge land on the shoulder tip? Note: ______.

## 7. Time and yield log

I need real numbers to replace my guesses in `VIABILITY.md`. Fill this in as you go with a stopwatch. Count **hands-on minutes only** (not waiting for prints or glue). Note whether it was your first attempt: the first time is slow, so if you can, time a second repeat of the assembly steps too.

| Step | Minutes, first try | Minutes, repeat | What I assumed (bare collar) |
|---|---|---|---|
| Deburr and clean the printed parts (two skin pieces, lip, bar, clip, cover) | ____ | ____ | 15 (for all four skin pieces and lips) |
| Scuff and wipe the glue surfaces | ____ | ____ | 5 |
| Form the skin and join the dovetails | ____ | ____ | 10 |
| Glue the lip segment (handling and clamping only) | ____ | ____ | 15 |
| Glue the bar (handling and clamping only) | ____ | ____ | 14 per module |
| Fit the spring plunger and check the clip | ____ | ____ | (in the 14 per module) |
| Rework, trimming, fixing mistakes | ____ | ____ | 10 |
| Quality check: slide test, snap test, pull test | ____ | ____ | 25 |
| **Total hands-on assembly** | ____ | ____ | **85 for the bare collar** |

Print attendance (loading, starting, checking, unloading), per print job:

| Part | Minutes of attention |
|---|---|
| flat_skin_fr | ____ |
| flat_skin_br | ____ |
| hoop_lip_right | ____ |
| hoop_bar_cup | ____ |
| module_clip_coupon | ____ |
| diffuser_fitted_fr | ____ |
| I assumed about 7 minutes per job | |

Yield, which sets how much waste to build in:

| Part | Prints attempted | Prints that came out usable | Grams wasted |
|---|---|---|---|
| flat_skin_fr | ____ | ____ | ____ |
| flat_skin_br | ____ | ____ | ____ |
| hoop_lip_right | ____ | ____ | ____ |
| hoop_bar_cup | ____ | ____ | ____ |
| module_clip_coupon | ____ | ____ | ____ |
| diffuser_fitted_fr | ____ | ____ | ____ |

I assumed about 12% of prints fail. Also note: actual printing hours per part ____, total filament used ____ g (I estimated 88 g), glue cure time actually needed ____ h, and anything that took longer than you expected: ______.

## 8. Gate

Stage 1 passes only when **all** of these are true:

- [ ] The flat TPU pieces came out clean and bend without damage.
- [ ] The dovetails join and hold.
- [ ] The bar's glue joint holds at 90 N.
- [ ] The clip slides on with light force, does not bind, and cannot lift off.
- [ ] The cover snaps onto the lip and stays on.
- [ ] The formed piece holds a cone shape well enough to carry on.

If the cone does not hold its shape, that is the biggest unknown in the design: stop and send me what you saw. The fallback is a stiffer skin or a thicker skin, not a reprint with different settings.

## 9. Send back to me

- Photos: each printed part, the glued assembly from above and from the side, the clip on the bar, the cover on the lip, and anything that failed.
- Every blank above filled in, including the time and yield log, plus the printer, the filament brands and the settings you used. I will use the log to redo the cost and break-even numbers in `VIABILITY.md` with your real times.

## Safety for this stage

- Adhesive: gloves, ventilation, keep it off your skin and eyes.
- Pull test: eye protection, and hold the part so nothing flies if it lets go.
- Deburr before anyone handles it.
- No cell, board or strip yet. Do not wear anything until Stage 2.
