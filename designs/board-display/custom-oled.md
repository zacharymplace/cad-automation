# Specify an OLED without changing the product registry

Board-display JSON designs accept an optional `display` object. Existing designs
continue to use their registered display. A supplied display replaces that
reference for assembly generation, enclosure geometry, inspection, and analysis.
The Pico calibration fixture also accepts this object at `parameters.display`.
Both workflows default to the reference display when it is omitted.

The following dimensions are a synthetic example, not a recommended commercial
module or physical acceptance evidence:

```json
{
  "schema_version": "1",
  "product": "PICO2_OLED",
  "parameters": {"display_z_mm": 9.0},
  "display": {
    "identifier": "SYNTHETIC_EXAMPLE",
    "module_width_mm": 30.0,
    "module_height_mm": 25.0,
    "module_depth_mm": 5.0,
    "active_width_mm": 22.0,
    "active_height_mm": 11.0,
    "geometry_source": "synthetic example; replace with drawing or measurement reference"
  }
}
```

Dimensions are millimeters. The module depth must include the complete hardware
stack. Optional active-area center offsets, mounting-hole diameter and X/Y
spacing, clearances, and PCB/panel layers use the core DisplaySpec field names.
Mounting-hole dimensions must be supplied together; layered geometry requires
PCB thickness and panel width, height, and thickness. Unknown fields, nonfinite
numbers, incomplete dimensions, and active areas outside the module are rejected.

The evidence label defaults to `reference`. A source string records provenance;
it does not certify its truth or prove physical fit. Record physical acceptance
separately after obtaining and measuring the actual hardware.

Save the design, then use `zcad design validate`, `zcad design inspect`, and
`zcad design analyze` with its path before enclosure export. Inspect reports the
selected display dimensions and source. Set placements from the actual stack;
changing dimensions alone does not automatically reposition the display.
