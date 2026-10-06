# Explicit OLED retention in the Pico calibration enclosure

Set `parameters.display_retention` to `clips` to add the core's existing lid-hung
retainer: four L-shaped corner guides and two side clips that hook beneath the
module. The center of each Y edge remains open for a header or flex cable.
The lid plate stops upward motion. This implementation currently supports
solid-envelope display models; layered PCB/glass modules require PCB-specific
supports and are rejected. Mounting-hole metadata does not create screw posts.

The default is `none`, so prior design files and acceptance packages keep their
original geometry. There are two explicit demonstration inputs:

- calibration/pico2-oled-clips-reference.json: generic reference OLED, not a
  selected commercial module.
- calibration/pico2-oled-clips-synthetic.json: larger, thicker synthetic OLED
  with an offset active area; not hardware measurements.

Both use the existing core DisplayRetainerParameters and add_display_retainer.
No core implementation is duplicated or modified. Parameters in millimeters:

| Parameter | Default | Meaning |
| --- | --- | --- |
| retention_clearance_mm | 0.3 | Module-to-guide clearance per side |
| retention_wall_mm | 1.2 | Guide and clip stem wall |
| retention_clip_reach_mm | 1.0 | Lip reach from the guide's inner face |
| retention_clip_lip_height_mm | 1.0 | Lip thickness under the module |
| retention_clip_gap_mm | 0.1 | Gap below the installed module |

Lip reach must exceed guide clearance. The remaining core dimensions are its
3 mm corner legs, 2.5 mm pads, and 6 mm clip width. The enclosure reserves room
for the retainer outside the module and conservatively solves component clearance
using its entire bounding footprint down to the clip bottoms. The display and
body can rise to prevent clips from reaching board components. Generation rejects
retainer contact volumes with hardware or the enclosure body. Touching intended
stop surfaces without volumetric overlap is allowed.

For the reference input, body dimensions are 36 x 59 x 13.1 mm; the lid's total
bounds are 36 x 59 x 7.9 mm, including the clips below its locating lip. The
assembled height is 15.9 mm. The larger lid bounds do not add directly to the
body height because the retainer sits inside the body.

```sh
cd /Users/zplace/dev/cad-automation
.venv/bin/python -m zcad.cli accept designs/calibration/pico2-oled-clips-reference.json --revision pico2-oled-clips-004 --output exports/acceptance/pico2-oled-clips-004
.venv/bin/python -m zcad.cli accept-verify exports/acceptance/pico2-oled-clips-004
```

The report checks six small cardinal translations of the module against the
seated lid: X/Y moves exceed guide clearance by 0.1 mm, downward motion exceeds
the clip gap by 0.1 mm, and upward motion is 0.1 mm. A positive stop intersection
is required in every direction. Installed hardware collisions, lid/body overlap,
window obstruction, STEP reimport, and STL topology remain separate checks.
A missing clip must fail retention; disabling retention leaves it NOT_CHECKED.

These probes establish modeled translational stops only. They do not certify
clip flex, insertion/removal, rotational escape, strength, fatigue, printer
accuracy, or actual header/cable clearance. Record these after obtaining exact
hardware and a controlled physical print. No physical result is claimed.
The core retainer is designed for a lid printed outer-face down; establish actual
orientation, supports, slicer settings, and material during that print test.


The cable insertion fixture at
`calibration/pico2-oled-clips-usb-test-envelope.json` exercises the USB housing
and nose check. Its source is marked `test_envelope`: it is not a measured cable. See [pico2-usb-plug.md](pico2-usb-plug.md)
for the required measurements. Replace the full `usb_plug` object with measurements
or an identified vendor drawing before treating those results as evidence for a real cable. The housing
is a rectangular overmold; the nose is a rectangular mating envelope. No flexible
cable bend or tapered transitions are modeled.
