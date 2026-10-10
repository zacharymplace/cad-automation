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
- LED diffuser cover: thin curved cover over the LED channel (8.8 mm wide at its narrowest, fits an 8 mm strip), outer hook grips the lip. 4 quarters, ~35 g. Friction fit, not a snap: untested.
- Dovetail tabs and pockets (0.25 mm clearance) join the four quarters: two per side seam, one on the back. `build.py` checks for overlap and loose crumbs.

- `module.py`: two clip-on modules on the same 56 mm clip with two M3 retention screws. Cup cradle at front-right (ring at upper-chest height, side opening so the cup slides out toward the hand, 77 g). Phone cradle at front-left (snaps in from the wearer side, open back window, 8 deg tilt so the screen tilts up, 84 g). Both checked clear of the yoke and the mannequin torso.

## Not done yet
- More modules (phone, fan arm, ear-defender mount); translucent LED diffuser cover; module pocket is position-specific (right side, rail at 0.82), other spots need regenerating.
- Cup ring sits ~75 mm in front of the chest. The longer clip and screws should resist prying, but that is unproven until a print is tried with a full cup.
- Joints are untested in print: tune `joint.clearance` after the first TPU test. They hold the parts in plan only; add glue or a pin if the seam lifts.
- Fit test: print one quarter in TPU first.
- Weight is a 100%-solid upper bound, not a slicer estimate.
