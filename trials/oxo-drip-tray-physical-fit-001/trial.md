# OXO Drip Tray Physical Fit Trial 001

## Purpose

Validate the OXO soap-dispenser drip tray design through one
controlled physical print and fit review.

## Source evidence

- designs/oxo-soap-dispenser-drip-tray.json
- src/zcad/generators/drip_tray.py
- src/zcad/generators/drainage_basin.py
- commit 2767450 (Refine drip tray spout and extract shared drainage basin)

## Required observations

- slicer profile
- material
- layer height
- basin print result
- grid print result
- basin-to-grid fit (does the grid seat flush on the wall tops)
- OXO dispenser base fit on the grid (clearance, wobble, footprint)
- counter-edge placement and spout overhang into the sink
- drainage behavior (does water actually run off the curved tip)
- drip-break groove effectiveness (does water still wick back under the spout)
- visible defects
- dimensional or fit deviations

## Decision

Pending physical test.

Allowed outcomes:

- accept
- revise
- reject

## Boundary

No production-readiness claim is permitted from this trial.

A successful result proves only the tested configuration,
printer, material, slicer settings, and physical sample.

The basin and grid are software-validated only prior to this
trial: drainage behavior, counter-edge fit, dispenser fit, and
printability are unverified until this trial is completed.
