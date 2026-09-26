# Garden layout catalog

These assembly inputs use the existing `garden-assembly` command. Each
layout repeats the same 40 mm module at 40 mm pitch, with 0.25 mm rail
clearance. All remaining module dimensions use generator defaults.

| Layout | Input | Modules | Connections | Overall bounds (mm) |
| --- | --- | ---: | ---: | --- |
| Heart | `garden-heart.json` | 16 | 21 | 203 × 203 × 40 |
| L-shaped corner | `garden-corner.json` | 6 | 5 | 163 × 123 × 40 |
| Rectangular bed | `garden-bed.json` | 12 | 17 | 163 × 123 × 40 |
| Ring (existing example) | `garden-assembly.example.json` | 8 | 8 | 123 × 123 × 40 |

Bounds include projecting connectors. The SVG shows schematic footprints;
STEP is the geometry reference. “Bed” describes the layout, not a larger
module or an evaluated planting capacity.

## Build all three new layouts

From the repository root, using a new output parent:

```bash
cd ~/dev/cad-automation || exit 1

zcad_catalog_trial="$(mktemp -d "$HOME/Downloads/zcad-catalog-trial.XXXXXX")" &&
for layout in heart corner bed; do
  .venv/bin/python -m zcad.cli garden-assembly \
    "designs/garden-$layout.json" \
    --output "$zcad_catalog_trial/$layout" || break
done
printf '\nCatalog output: %s\n' "$zcad_catalog_trial"
```

Each successful build writes `assembly.step`, `layout.json`, `report.json`,
and `assembly-preview.svg`. Inspect both collision and insertion status in
the report. Export success alone does not mean insertion passed.

## Evidence and limits

The three new layouts were built with CadQuery 2.8.0. Collision and vertical
insertion checks passed; STEP reimport recovered the expected solid counts;
preview numbering matched the report and artifact hashes matched the files.
This is nominal geometry evidence, not physical fit, strength, drainage or
plant suitability validation. The selected insertion order is one valid
order under the checker assumptions, not a required order for these layouts.

`X` places a module and `.` leaves a cell empty. Row zero is at +Y. Keep
rows rectangular and the filled cells connected through shared edges.
Use this command for assembly JSON; these files are not individual product
designs for the gift-bundle command.
