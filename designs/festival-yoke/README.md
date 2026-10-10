# festival-yoke

Parametric, printable shoulder yoke for festivals. Design rule: nothing rises above the shoulders, so nobody's view is blocked.

```
uv run --no-project --with cadquery build.py     # out/*.stl + weight/bed report
uv run --no-project --with cadquery view.py      # out/viewer.html (serve: python3 -m http.server -d out)
```

Edit `config.toml` (measure the wearer), rerun.

## v1
- Sloped 2 mm TPU skin on the trapezius, open front to flex over the head, lightening slots. 4 quarters.
- T-rail round the sides and back for clip-on modules (cup, phone, fan arm, ear-defender mount).
- Outer lip forming an LED-strip channel between lip and rail.
- Dovetail tabs and pockets (0.25 mm clearance) join the four quarters: two per side seam, one on the back. `build.py` checks for overlap and loose crumbs.

- `module.py`: cup cradle that snaps onto the rail at front-right (55 deg). The ring hangs at upper-chest height with a side opening, so the cup slides out toward the hand. 56 mm long clip with two M3 self-tapping retention screws into the rail stem, 76 g solid; checked clear of the yoke and the mannequin torso. Change `ANGLE`, `HANG`, `OPEN`, `LENGTH` at the top of the file.

## Not done yet
- More modules (phone, fan arm, ear-defender mount); translucent LED diffuser cover; module pocket is position-specific (right side, rail at 0.82), other spots need regenerating.
- Cup ring sits ~75 mm in front of the chest. The longer clip and screws should resist prying, but that is unproven until a print is tried with a full cup.
- Joints are untested in print: tune `joint.clearance` after the first TPU test. They hold the parts in plan only; add glue or a pin if the seam lifts.
- Fit test: print one quarter in TPU first.
- Weight is a 100%-solid upper bound, not a slicer estimate.
