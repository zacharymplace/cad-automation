# Explicit build-volume orientation

Policy schema 1.0 remains generated-orientation only. Schema 1.1 requires
`build_volume_orientation`: `generated` or `xy_90`. The latter permits either
the generated orientation or a 90-degree turn about Z for each part separately.
The catalog example explicitly opts into `xy_90`; warning rejection stays enabled.

The build_volume check records original bounds, printer limits, generated_status,
xy_90_status, rotated bounds, orientation_policy, and selected_rotation_z_degrees.
Selection is 0 when generated bounds fit, 90 when only the permitted alternative
fits, and null if neither permitted orientation fits. Missing limits or geometry
remain NOT_CHECKED. The check status and evaluated_status reflect the selected
policy; generated_status preserves the original-orientation finding.

Validation does not rotate source geometry or write CAD exports. Existing export
calls retain generated-orientation checks. This is a per-part bounding-box test,
not a bed-packing, support, brim, strength, physical-fit or printability check.
Z is unchanged. No tolerance is added to build-volume limits.

Run validate or validate-catalog with --policy designs/validation-policy.example.json.
Old receipts are unchanged. The expanded catalog previously recorded 36 PASS,
7 FAIL, 0 ERROR. Five reported bounds fit after an XY turn; a fresh local run must
confirm the implementation on the actual designs. The two label-size warnings
are deliberately retained and are expected to keep the catalog gate failing.
