# Coupon opening validation

`zcad validate` and `zcad validate-catalog` automatically evaluate
`coupon_opening_clearance` for `tolerance_coupon`. Each hole and slot has a
stable feature ID and a separate result. Any obstruction failure fails the
report and policy even when the policy does not require this check explicitly.
Use `--require-check coupon_opening_clearance` for a coupon-only validation
command. Other design types report NOT_CHECKED; do not require this code in a
mixed catalog until those types have their own contracts.

Each nominal circular or capsule profile is extruded through the declared
centered plate interval. Its intersection with every solid in the main part is
measured. Residual material above 1e-6 cubic millimetres fails. Geometry or
intersection errors fail closed. This is a continuous volume check, not a grid
of point samples; material below the numerical tolerance can remain undetected.

The contract assumes the coupon generator's native coordinates and derives
opening locations from effective dataclass parameters (including defaults).
The clearance check establishes absence of material inside expected openings;
the complementary band check below establishes surrounding material coverage.
Neither verifies label clearance, physical fit, or print readiness. Export metadata retains
its existing core-only validation scope; these additional checks currently run
only in the two read-only automation validation commands.

Regression fixtures cover the real coupon, half-depth blockages, 0.02 mm internal
membranes, complete blockage, missing openings, and obstructions in separate
Workplane stack items. CLI and catalog failure propagation are also tested.

## Surrounding material

`coupon_surrounding_material` complements the empty-opening check. For every
hole and slot, a 0.2 mm outward band around the nominal profile must contain
material throughout the declared plate thickness. Reports identify the feature,
band width, expected volume, missing volume, method, and 1e-6 mm³ tolerance.
The band is a nominal geometry contract, not a printer minimum-wall rule.
It is not clipped to the plate or nearby openings: insufficient space for this
band fails the contract rather than silently reducing its coverage.

The checker subtracts each solid from the expected band. This tests coverage
by the union of all solids without double-counting overlapping or duplicate
solids. A shifted part, enlarged opening, or local cavity in the band fails.
Separate solids that collectively cover the band may pass; connectivity and
strength are not evaluated. Changes outside the band are outside this check.
Both coupon checks run automatically in read-only CLI and catalog validation;
other design types report NOT_CHECKED. Export validation remains unchanged.

This remains bounded nominal evidence, not a full dimensional inspection or
physical validation.
