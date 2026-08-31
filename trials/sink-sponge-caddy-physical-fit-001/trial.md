# Sink Sponge Caddy Physical Fit Trial 001

## Purpose

Validate the sink sponge-and-brush caddy design through one
controlled physical print and fit review.

## Source evidence

- designs/sink-sponge-caddy.json
- src/zcad/generators/sponge_caddy.py
- src/zcad/generators/drainage_basin.py
- commit b31bafb (Add sink sponge & brush caddy sharing the drainage basin)

## Required observations

- slicer profile
- material
- layer height
- basin print result
- rack print result
- basin-to-rack fit (does the rack seat flush on the wall tops)
- sponge slot fit (does a typical kitchen sponge sit upright without falling)
- brush hole fit (handle diameter clearance for the brushes/scrubbers on hand)
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

The basin and rack are software-validated only prior to this
trial: drainage behavior, counter-edge fit, sponge/brush fit, and
printability are unverified until this trial is completed.
