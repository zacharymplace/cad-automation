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
It establishes absence of material inside expected openings, not exact opening
size, surrounding material presence, label clearance, measured walls, physical
fit, or print readiness. Oversized openings can pass. Export metadata retains
its existing core-only validation scope; these additional checks currently run
only in the two read-only automation validation commands.

Regression fixtures cover the real coupon, half-depth blockages, 0.02 mm internal
membranes, complete blockage, missing openings, and obstructions in separate
Workplane stack items. CLI and catalog failure propagation are also tested.
