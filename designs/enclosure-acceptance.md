# Digital acceptance for each Pico enclosure revision

Run `zcad accept` against the revision's calibration design, with an explicit
revision label and an empty output folder. The command builds and checks the
geometry, then writes report.json, a readable report.md, the exact design.json,
and STEP/STL parts if the geometry checks pass. Existing folders are never
replaced. The current scope is `pico2_enclosure_fit`, including custom OLED input.

```sh
cd /Users/zplace/dev/cad-automation
.venv/bin/python -m zcad.cli accept designs/calibration/pico2-enclosure-fit.json --revision pico2-reference-002 --output exports/acceptance/pico2-reference-002
.venv/bin/python -m zcad.cli accept-verify exports/acceptance/pico2-reference-002
```

`accept` uses `designs/acceptance-profiles/pico2-digital-baseline.json` by
default. Select the stricter modeled plug/OLED scope with
`--profile designs/acceptance-profiles/pico2-plug-oled-model.json`. A selected
profile is copied into the package, hashed, evaluated against every matching
check, and shown in both reports. A required check that is absent or
NOT_CHECKED makes the profile fail and changes the digital outcome to
REVISION_REQUIRED. The modeled plug/OLED profile can pass with `test_envelope`
inputs; that means its declared geometry checks passed, not that the hardware
was measured or physically tested.

An acceptance profile may also declare a maximum assembled enclosure envelope.
The check compares the assembled CAD bounding-box width, depth, and height in
millimeters against those limits. Profiles without the constraint keep their
existing behavior. The envelope is a digital size limit; it does not represent
printer accuracy, manufacturing tolerance, or physical fit.

The default `pico2-digital-baseline` profile now opts in with a 40 × 65 × 20 mm
maximum. The stricter modeled plug/OLED profile uses 45 × 60 × 25 mm to contain
the repository's larger synthetic OLED/clip design (44 × 59 × 20.4 mm) with
rounded digital headroom. That fixture is synthetic, so this is not a measured
hardware or customer requirement.

```json
{
  "schema_version": "1.2",
  "required_checks": [],
  "fail_on_warnings": false,
  "maximum_enclosure_envelope_mm": {
    "width": 40,
    "depth": 65,
    "height": 20
  }
}
```

Use a new folder and label for every revision. The revision label is a human
identifier; the report binds the actual design bytes, product/core source files,
Git HEAD and working-tree state, software versions, and output hashes. Changed
sources or design bytes during generation reject the run. Keep source checkouts
stable while generating reports. A dirty tree is recorded, not treated as a
committed revision. Export bytes can differ between repeated CAD exports; the
design/source hashes, dimensions, and checks identify repeatable inputs/results.

Checks cover valid solid geometry, catalogued board/display collision and
clearance, conservative display vertical gaps, USB boundary clearance, every
modeled component against the body and seated lid, body/lid overlap, nominal
mounting bores, the rounded display opening, and a connector-sized straight USB
path. Each exported body/lid STEP and STL is checked against its source geometry.
STEP is reimported and checked for a single valid solid, matching bounds and
volume, and the symmetric-difference volume between source and reimported
solids. This catches localized shape changes that preserve overall bounds and
volume. Binary STL is checked for closed, consistently wound topology and
matching bounds/volume within recorded tessellation tolerances. It is also
compared with the source solid by deterministic 3D Halton occupancy samples;
the report records the sample count, mismatches, sampled region, estimated
symmetric-difference volume, and tolerance. This is an approximate comparison:
localized differences smaller than the sample spacing can be missed. Controlled
tests use a 20 mm cube with an equal-size cubic cavity moved among three
locations, preserving outer bounds and total volume. With 2,048 samples and a
0.5% source-volume threshold, cavities up to 2.5 mm per side were not detected
at those locations; a 3 mm cavity was detected at all three. At 512 samples, one
of the three 3 mm cases was missed; 1,024 and 2,048 detected all three. The
2,048-sample setting is retained for margin, while the measured boundary applies
only to these fixtures and locations. The report contains the resolved
parameters, hardware specifications, component placements, source declarations,
dimensions, measurements, and each check's result.

A result of DIGITAL_CHECKS_PASSED means the evaluated digital checks passed.
With `usb_plug` supplied, the report records its housing and nose dimensions,
source label, seated fit, nose fit against the modeled receptacle, and a continuous
straight translation sweep. `evidence_status` must say `measured`,
`vendor_drawing`, or `test_envelope`. These are user supplied labels, not
independently verified sources. Without `usb_plug`, plug fit and insertion remain
NOT_CHECKED. The overmold is modeled outside the wall; its narrower nose crosses
the opening into the modeled receptacle. Flexible cable bend, strain relief
curvature, tapered transitions, and actual physical insertion remain NOT_CHECKED.
The insertion result states its method and assumptions: axis-aligned rectangular
housing/nose envelopes, straight negative-Y translation without tilt or rotation,
and receptacle bounds represented by its modeled axis-aligned bounding box. A
PASS applies only to that nominal envelope sweep; it does not establish that a
real plug can be physically inserted. Cable, strain relief, chamfers, latches,
and manufacturing variation are omitted.
Clip flex/holding strength and printed fit also remain NOT_CHECKED. OLED retention
is NOT_CHECKED when disabled. With
`display_retention: "clips"`, six cardinal translation probes check modeled
stops and record their intersection volumes; this does not prove rotational
restraint, insertion feasibility, fatigue resistance, or physical holding strength. Physical status remains PENDING. No printer profile, material
process, or slicer setting is accepted by this command. When `usb_plug` is omitted, the existing connector-envelope check remains available.
See [pico2-usb-plug.md](pico2-usb-plug.md) for the exact measurement fields
and their coordinate meaning.

Invalid inputs or geometry produce REVISION_REQUIRED with a specific failure
and process exit code 1. Failed runs can contain diagnostic/partial exports;
these are not accepted for use. Unsupported designs are rejected with a saved
failure report. Setup errors such as unreadable files or occupied output folders
fail without overwriting existing results.

`accept-verify` reports `package_integrity`, `report_consistency`, and
`acceptance_outcome` separately. It exits 1 when files are changed or missing or
when the report contradicts its check results or export inventory. An unchanged,
internally consistent package whose `acceptance_outcome` is `REVISION_REQUIRED`
still has passing integrity and consistency. Integrity is checked relative to
report.json. The verifier also reports the exact `report_sha256`; record that
digest outside the package through a trusted channel, then pass it as
`--trusted-report-sha256 <digest>` to check for `MATCHED_TRUSTED_SHA256`.
Without an independently trusted digest authenticity remains `UNVERIFIED`; a
mismatch fails verification. This pins the exact report bytes but does not rerun
geometry or identify a signer. Preserve the report and trusted digest in a
trusted revision record.
Source provenance declarations and hashes do not establish actual measured
hardware or permission to use a vendor model.

Test fixtures cover the baseline and stricter acceptance profiles, the larger synthetic OLED with an
offset active area, invalid parameters, an intentionally obstructed window and
USB insertion path,
source drift, repeated runs, artifact tampering, and overwrite protection.
