# Pico 2 enclosure: current-core fit test

## Scope and source

This test uses `designs/calibration/pico2-enclosure-fit.json` and the installed
editable `zcad-core` checkout. The reconciliation was prepared against core
revision `744542a6e5d4fd242b9de6e429005cdfe9300297`. Record the actual source
revisions, uncommitted source hashes, and export hashes with each test package;
export metadata's base Git commit alone does not identify uncommitted changes.

The acceptance rerun pins core revision
`ee0f0084e3245b7b49c7232770a988c237418102` in a detached checkout because the
canonical core advanced during the first full verification. Its intervening
changes concern stackable latches, not the Pico assembly or component catalog.
Use the verified core checkout's `src` on `PYTHONPATH` when reproducing that
package. The receipt records the imported checkout and exact test commands.

The core now includes the Pico 2's catalogued board components. Assembly analysis
must retain those components and their display clearance checks. The fit
assembly uses the core's component-aware display-height solver. Requested
`internal_height_mm` is a minimum: body and cavity height increase when necessary
to contain the raised display. The complete hardware must clear the body and
seated lid, and the body and lid must not intersect.

Generate a fresh package from the product repository:

```bash
cd /Users/zplace/dev/cad-automation
.venv/bin/python -m zcad.cli designs/calibration/pico2-enclosure-fit.json \
  --printer-profile profiles/printers/prusa-mk4.json \
  --material-profile profiles/materials/petg.json \
  --output exports/pico2-current-core-001
```

The Prusa/PETG profiles are provisional digital validation inputs, not a record of
an available printer or a physical print. The operator reported no printer
available on 2026-10-02. Physical validation remains blocked until a printer or
print service and the actual board/display/cable are available. The OLED in this
model is `REFERENCE_OLED_128X64`; confirm dimensions of the actual module before
printing. Do not assume compatibility with every 128x64 OLED.

## Physical test record

Create a dated record referencing the exact body/lid export hashes. Leave
unobserved fields pending; software PASS is not physical acceptance.

- Test ID, operator, date, source/package revision, STEP/STL hashes.
- Actual Pico 2 variant, OLED make/model, module measurements, cable/plug.
- Printer model, nozzle, material brand/type, slicer name/version.
- Slicer preset and saved project/configuration; layer height, wall count,
  infill, temperatures, supports, orientation, and any XY compensation.
- Sliced preview checked for missing features, unsupported regions, and sealed
  openings. Record any deliberate geometry or profile changes as a new revision.
- Body and lid print outcome; defects, print time, material, failed attempts.
- Lid seats fully without forcing, cracking, or contacting electronics; record
  measured clearance, retention, and removability. The design has no implied
  waterproof or rated enclosure claim.
- Board holes align with all standoffs; record fastener size and mounting result.
- Display fits and its active area is visible; record module-to-board and lid
  clearance with photos/measurements.
- USB plug inserts fully through the opening; record cable clearance and whether
  the board, standoffs, or wall obstruct access.
- Outcome: ACCEPT FOR THIS HARDWARE / REVISE / REJECT, with observed reasons and
  the next revision. One passing print does not establish production readiness.

## One-customer test after physical acceptance

Use a customer-owned, specific enclosure need. Confirm the board/display/ports,
mounting environment, dimensional limits, and acceptance criteria before quoting.
Do not present the reference enclosure as a proven fit for different hardware.
Exclude safety-critical or certification-dependent applications from this test.

Record separately:

- The customer's existing workaround, consequence, and specific required result.
- Quote, scope, revision limit, acceptance conditions, and actual customer
  commitment. Stated willingness to pay is not a payment.
- Measurement, modeling, validation, and support time; outsourced print cost,
  material, postage, reprints, and each cause of revision.
- Delivery and customer fit/use observations, money received, and total delivery
  cost. Compare net revenue with actual labor time before promising a repeatable
  price or expanding the offer.

Do not send outreach, order a print, or record a sale merely because this runbook
exists. Those actions need a real recipient/provider and the applicable scope.
