# Pico calibration with a custom OLED

Supply the same display specification accepted by the general board-display
workflow under `parameters.display`. Required fields are identifier, module
width/height/depth, active width/height, and geometry_source. Optional active
center offsets and PCB/panel layers retain their core meaning. Dimensions are
millimeters; sources and evidence labels do not establish physical acceptance.

The generator uses this hardware for component-aware display elevation, body
width/depth/height, and the offset lid window and bezel. Pico board components,
standoffs, and USB access checks remain in the assembly. Omitting display keeps
the existing reference. Module mounting metadata does not add OLED screw posts. Optional
`display_retention: "clips"` uses the core corner guides and side clips for
solid-envelope modules; see ../pico2-oled-retention.md. Layered modules require
PCB-specific support and are rejected for this clip option.

`pico2-custom-oled.synthetic.json` demonstrates a larger, thicker module with
an offset active area. It is a software test example, not a commercial hardware
recommendation or physical fit result. Generate with:

```sh
cd /Users/zplace/dev/cad-automation
.venv/bin/python -m zcad.cli designs/calibration/pico2-custom-oled.synthetic.json --output exports/pico2-custom-oled-synthetic
```

Before a physical print, replace the synthetic data with the exact selected
module and its drawing/measurements, record cable and pin envelopes, regenerate,
and verify the resulting assembly. Printed fit and customer payment remain
separate evidence gates.
