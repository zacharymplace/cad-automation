# Measuring for the yoke

Five measurements, a soft tape, a ruler and a helper. About ten minutes. Write them in millimetres (1 cm = 10 mm).

Stand relaxed, shoulders down, no jacket or thick top.

| # | Measure | How | Config name |
|---|---------|-----|-------------|
| 1 | **Head circumference** | Tape round the head just above the eyebrows and ears, over the widest part at the back. | `head_circumference` |
| 2 | **Neck circumference** | Tape round the base of the neck, where a shirt collar sits. Snug, not tight. | `neck_circumference` |
| 3 | **Shoulder width** | Across the back, from the bony tip of one shoulder to the bony tip of the other. Straight line, not following the curve. | `shoulder_width` |
| 4 | **Shoulder depth** | Front to back over the top of the shoulder, halfway between neck and shoulder tip. Hold a ruler on the collarbone and read the distance to the back of the shoulder, or have your helper measure it from the side. | `shoulder_depth` |
| 5 | **Shoulder drop** | Height from the neck base to the shoulder tip. Lay a ruler flat on top of the neck base, level with the floor, and measure straight down to the shoulder tip. | `shoulder_drop` |

Typical adult ranges, for a sanity check (5th to 95th percentile, men and women pooled, from the ANSUR II survey: see SIZING.md): head 537-600, neck at the base 345-480, shoulder width 342-441. Shoulder depth and drop are not surveyed in this form; expect about 200-300 and 35-60.

## Choosing a size

Presets in `config.toml`:

| Size | Head | Neck | Shoulder width | Depth | Drop |
|------|------|------|----------------|-------|------|
| S | 550 | 365 | 350 | 230 | 36 |
| M | 570 | 380 | 380 | 260 | 40 |
| L | 580 | 425 | 410 | 280 | 45 |
| XL | 590 | 450 | 440 | 300 | 51 |
| XXL | 595 | 480 | 470 | 320 | 57 |

The presets were checked against the ANSUR II survey (SIZING.md): they cover about 98% of adults in that sample, but it is a US Army sample, so treat them as starting points. XXL is for shoulders around 460-490 mm, which the Army sample barely contains (about 1% of it), so it rests on extrapolation: the dimensions follow the same proportions as the other sizes. Neck means the circumference at the base of the neck where a shirt collar sits, not at the Adam's apple. Shoulder width is the one that matters most: the yoke should sit on the shoulders, not hang off them. If you are between sizes, go by shoulder width and neck, not head.

If your numbers are not near a preset, use your own:

1. In `config.toml` set `size = "custom"` and fill in `[custom]` with your five measurements.
2. Run `uv run --no-project --with cadquery build.py`.
3. Read the fit report it prints. Lines starting `WARN` mean the opening is loose or tight, or the collar is too narrow for the docking bars.

The head and neck numbers set the opening. The opening is wider than the head by 19 mm each side (ease plus about 10 mm for hair), and about 87% of the head's length front to back. The head tilts through the open front to go on, so the opening is deliberately not a full ring.

## Check the fit before printing the rest

The numbers only get you close. Before printing everything, print one quarter and hold it against a real shoulder:

- Does it lie flat on the shoulder and follow the slope?
- Is the opening roughly centred on the neck, with room at the sides?
- Does the collar edge land on the shoulder tip, not past it?

If it floats at the tip, raise `shoulder_drop`. If it sits on the shoulder tip but lifts at the neck, lower it. Change one thing at a time and rebuild.

## Printer bed

All parts of S, M and L fit a 220 mm bed (from L up the lip segments are split in two). XL needs a bed of about 232 mm and XXL about 250 mm, set by the flat skin pieces; `build.py` prints the smallest square bed that fits every part. Set `bed` under `[print]` to your printer's size and it will flag anything that does not fit.

## Build every size at once

```
uv run --no-project --with cadquery build_all.py
```

Prints one table: weight, bed fit, joint overlap and loose-crumb checks for each preset. Outputs for each size go in `out/<size>/`.
