# festival-yoke

Parametric, printable shoulder yoke for festivals. Design rule: nothing rises above the shoulders, so nobody's view is blocked.

```
uv run --no-project --with cadquery build.py     # out/*.stl + weight/bed report
uv run --no-project --with cadquery view.py      # out/viewer.html (serve: python3 -m http.server -d out, then open /M/viewer.html); `concept.py` makes the four-panel concept sheet `out/M/concept.png`
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

## Not done yet
- More modules (phone, fan arm, ear-defender mount); translucent LED diffuser cover; module pocket is position-specific (right side, rail at 0.82), other spots need regenerating.
- Dock and fan are concept-level: defender size varies a lot, and the fan has no power source (USB lead to a bank in a pocket for now).
- Cup ring sits ~75 mm in front of the chest. The longer clip and screws should resist prying, but that is unproven until a print is tried with a full cup.
- Joints are untested in print: tune `joint.clearance` after the first TPU test. They hold the parts in plan only; add glue or a pin if the seam lifts.
- Fit test: print one quarter in TPU first.
- Weight is a 100%-solid upper bound, not a slicer estimate.
