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
Neither verifies label clearance, physical fit, or print readiness. Application CLI exports and fresh bundle builds also run these checks before
creating the output directory or writing artifacts. The combined report is
returned in ExportResult and stored as design_validation in part metadata.

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
other design types report NOT_CHECKED. The application registers the same checker on both CLI export paths. Direct
core export callers must explicitly supply feature_validator; core does not
import application-specific geometry rules. Existing exports used with
--skip-build are not regenerated or retrospectively feature-validated.

This remains bounded nominal evidence, not a full dimensional inspection or
physical validation.

## Export failure behavior

Core runs the application hook against isolated copies of the inspected shapes,
before filesystem writes. FAIL results, exceptions, malformed results, and
non-JSON evidence block export. Existing artifacts remain untouched on validation
failure. This is pre-export geometry evidence; STEP round-trip evidence and
publication behavior are described below.

## STEP round-trip evidence

When an application feature validator is registered, core stages every STEP in
an external temporary directory, reimports and inspects all parts, then runs the
same feature validator on those reimported shapes. A failed import, geometry
inspection, or feature check blocks publication before the output directory is
created or existing artifacts are changed. Temporary files are cleaned up.

The design report includes a separate `step_round_trip` object with status,
checks, scope, and `step_sha256_by_part`. The exact staged bytes are published;
STEP is not regenerated after checking. Both coupon opening clearance and
surrounding material must pass. Unsupported designs report `NOT_CHECKED` for
feature coverage, even though STEP reimport and geometry inspection occurred.
Direct core calls without a feature validator retain their previous behavior.

These results do not establish full geometric equivalence, STL fidelity,
physical fit, or print readiness. STEP bytes are held in memory until publication.

## Export-set publication

All STEP, STL, and metadata files for the request are generated in temporary
storage before publication. Metadata and returned paths reference the final
destination. A late STL or metadata failure leaves the destination unchanged.

Publication prepares incoming files and backups beside the destination so file
replacement stays on the same filesystem. A caught replacement failure restores
previous files and removes newly published files. Unrelated files are preserved;
stale files outside the current request are not removed. Symbolic-link output
directories and symbolic-link or non-file targets are rejected.

If rollback itself fails, the operation raises an explicit recovery error and
retains its backup directory. Do not delete that directory before recovery.
Successful publication and successful rollback remove publication staging.

This is a single-writer contract. It provides rollback for caught failures, not
crash/power-loss recovery or atomic visibility across the whole file set.
Concurrent readers can observe replacement in progress; concurrent writers are
unsupported. Newly created ancestor directories may remain after a failed
publication setup. No claim of filesystem durability is made.
# STL round-trip validation

Exports inspect the staged binary STL before publication. The metadata's
`design_validation.stl_round_trip` records the inspected byte SHA-256 per part,
triangle count, signed volume, topology results and registered feature probes.
The inspected file is the file published; no repair or regeneration follows.
Any mesh or probe failure rejects the complete export set before publication.

Topology requires finite coordinates, nondegenerate unique triangles, exactly
one opposite directed partner for every edge, and positive total signed volume.
Vertices are matched exactly. ASCII STL is outside this exporter contract.
Self-intersections, vertex manifoldness, component nesting and full shape
equivalence are not established by these checks.

For tolerance coupons, the CLI registers mesh occupancy probes for every hole
and slot: 16 angular locations, plus slot straight-side samples, at three Z
levels (-0.4, 0, +0.4 times plate thickness). Opening probes lie at 80% of nominal
radius; material probes lie 0.1 mm outside the nominal boundary. Opening centers
are also sampled. Ray parity uses two directions and fails on unresolved or
inconsistent classifications. This is sampled feature evidence, not the exact
continuous-volume BRep check: small defects between probes can remain undetected.
It does not establish exact opening dimensions, minimum walls or printability.

Other designs explicitly record feature `NOT_CHECKED`. Direct core callers must
register `stl_feature_validator` to obtain product probes. A topology PASS alone
does not claim that product features were checked. Read-only catalog checks do
not create STL files and therefore do not include this export-stage evidence.
