# festival-yoke

Parametric, printable shoulder yoke for festivals. Design rule: nothing rises above the shoulders, so nobody's view is blocked.

```
uv run --no-project --with cadquery build.py     # out/*.stl + weight/bed report
uv run --no-project --with cadquery view.py      # out/viewer.html (serve: python3 -m http.server -d out, then open /M/viewer.html); `concept.py` makes the concept sheets `out/M/concept*.png`
```

Pick a size in `config.toml` (`size = "M"`, or `custom`), or override per run with `FESTIVAL_YOKE_SIZE=L`. Measure the wearer first: see [MEASURING.md](MEASURING.md). Outputs go in `out/<size>/`; `build_all.py` builds S/M/L/XL and prints one comparison table.

## Sizes
S/M/L/XL presets and a custom option, driven by five measurements (`sizing.py`). All sizes pass the joint and cup-module clash checks. XL needs a ~235 mm bed; the others fit 220 mm. The fit report flags a loose or tight neck opening and a collar too narrow for the rail. It is geometry only, not tested on a body.

## v1
- Sloped 2 mm TPU skin on the trapezius, open front to flex over the head, lightening slots. 4 quarters.
- T-rail round the sides and back for clip-on modules (cup, phone, fan arm, ear-defender mount).
- Outer lip forming an LED-strip channel between lip and rail.
- Edge rounding (0.6 mm, auto-reduced if the CAD kernel struggles) on the neck and shoulder edges.
- Four skin-conforming foam seats on the underside (blue in the concept sheet), between the slots and clear of the seams.
- LED diffuser cover: thin curved cover over the LED channel (9.6 mm wide at its narrowest, fits an 8 mm strip), ~40 g in 4 quarters. A hook on its outer edge grips the lip and a two-step bead snaps into a 0.5 mm groove in the lip (press down to fit). The lip now stands on the skin, not on its feather edge. Snap force and TPU/PETG flex are untested: `snap_section.py` draws the cross-section.
- Dovetail tabs and pockets (0.25 mm clearance) join the four quarters: two per side seam, one on the back. `build.py` checks for overlap and loose crumbs.

- `module.py`: four clip-on modules on the same 56 mm clip with two M3 retention screws, built at fixed rail angles: cup cradle front-right (77 g), phone cradle front-left (84 g), ear-defender dock on the right side (65 g), fan on the left side (55 g). The dock is a bowl that parks one ear cup on the shoulder, with strap slots and a tether eyelet; set `DOCK_CUP` to your defenders. The fan frame holds an 80 mm 5 V fan aimed up and inward at the face; its top is 89 mm above the neck edge, about jaw height. All are checked clear of the yoke, the mannequin torso and each other.

## Power and light (`power.py`)
- **Power pod** at the back of the collar (32 g empty, balances the cup and phone at the front): holds a 60 x 40 x 10 mm protected pouch cell (about 4000 mAh) and a 32 x 22 x 6 mm USB-C charge/boost board. Lid on four M2 self-tapping screws, vented. USB-C, switch and charge-LED openings in one end wall; two lead slots in the floor drop onto the LED channel, one per strip half.
- **LED strip:** two halves from the pod round to the front gap, 850 mm in all on size M, 8 mm wide (5 mm on size S, whose channel is only 6.4 mm). `power.py` prints the estimated draw and runtime: about 1.3 h at full white and 3.6 h dimmed on M. Those assume a 10 W/m strip and a 1.5 W fan: check your parts.
- **Fitted diffuser:** the cover is cut away where each module's clip sits (the plain cover collided with all of them: found and fixed here). Print `diffuser_fitted_*.stl`, not `diffuser_*.stl`.
- `power.py` also runs 18 clash checks between every module, the strip, the fitted cover and the yoke.
- Lithium cells are a fire risk: use a protected cell with a boost board that has its own protection, never wrap cells in the collar, and keep the pod's vents clear. No cell or board has been tested here.

## Weight and balance (`balance.py`)
- Printed parts come to about 320 g on size M (thin skin printed near solid, modules at ~20% infill); what you carry on it is about 955 g with a full cup, a phone, one ear defender, the cell and board, the fan and the strip. The collar is the minor part of the load, so the biggest levers are the payload and the layout.
- The first layout (cup 55, phone 125, dock 0, fan 180, pod 270 deg) put the loaded centre of mass 90 mm off-centre (1.13 N*m of tipping torque). `balance.py` searches the module angles and the current layout (cup 40, phone 140, dock 225, fan 345, pod 300) brings it to 19 mm full and 30 mm with a light load (0.24 N*m), with the clips still 38+ deg apart. The cup post now also stands out far enough to clear the lip and the body at every size.
- Shoulder pressure on the foam seats is about 4.5 kPa when full, under typical backpack-strap pressure.
- Cutting the cup from 360 g to 250 g pulls the full-load offset to about 14 mm. Skipping the ear defender removes 250 g of payload and its 32 g dock.
- The dock sits back-left, behind the shoulder: that is the cost of balancing the front-heavy cup and phone, and it is harder to reach than a side mount. Move it with `DOCK_ANGLE` and rerun `balance.py` to see the cost.
- All masses are estimates: payload masses and fill factors are constants at the top of `balance.py`. Weigh your real parts.

## Kits and extra modules
Pick a kit with `kit = "full"` in `config.toml` or `FESTIVAL_YOKE_KIT=glow`. Module angles for each kit are tuned for balance by `balance.py --tune` and stored in `kits.toml` (per size).

| Kit | Modules | Printed g (M) | Loaded g | COM offset | Margin inside the foam seats |
|---|---|---|---|---|---|
| core | none: yoke, seats, rail, lip | 131 | 131 | 6 mm | 48 mm |
| glow | pod (strip + cover come with it) | 184 | 289 | 49 mm | 5 mm |
| carry | cup, phone, ID pouch, pod | 285 | 970 | 66 mm | 0 mm |
| comfort | dock, fan, pod | 242 | 637 | 66 mm | 8 mm |
| full | all seven | 349 | 1354 | 24 mm | 33 mm |

"Margin" is how far the loaded centre of mass is inside the rectangle spanned by the four foam seats (+-123 mm across, +-54 mm front to back); at or below zero the collar pitches or rolls and one side lifts off. The carry kit sits right on that edge with a full cup, so use a smaller cup or lighten the front there. Masses are estimates (see `balance.py`).

New small modules in `module.py`: ID card pouch (card window faces out, tether eyelet), hydration-tube C-clip (snap-in, narrower slit than the tube), blank mounting plate (M5 hole and four M3 holes, for your own attachments), and a rail cover that caps an empty stretch of rail. The last two are not in any kit: add their names to a kit's `modules` list. Everything that hangs below the collar now stands off the lip and the body by a computed distance, so side placements clear the torso.

`concept_kit.py` draws each kit; `out/M/kits.png` is the montage.

## Printing
`PRINT_PLAN.md` (made by `print_plan.py`) is the staged plan: material check, then a small fit pack (two yoke quarters, one cover quarter, a clip coupon), then the bare collar, then each module under load, then electronics on a bench. It lists slicer starting points and per-part orientation, support area and time. The yoke quarters need supports under the whole slope; the plan starts them in rigid PETG as a proxy before TPU.

## Not done yet
- More modules (phone, fan arm, ear-defender mount); translucent LED diffuser cover; module pocket is position-specific (right side, rail at 0.82), other spots need regenerating.
- Dock and fan are concept-level: defender size varies a lot, and the fan has no power source (USB lead to a bank in a pocket for now).
- Cup ring sits ~75 mm in front of the chest. The longer clip and screws should resist prying, but that is unproven until a print is tried with a full cup.
- Joints are untested in print: tune `joint.clearance` after the first TPU test. They hold the parts in plan only; add glue or a pin if the seam lifts.
- Fit test: print one quarter in TPU first.
- Weight is a 100%-solid upper bound, not a slicer estimate.
