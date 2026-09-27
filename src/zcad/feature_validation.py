"""Product-specific nominal opening checks for design validation and exports."""

import math

import cadquery as cq
from zcad_core.validation.design_report import validate_design as validate_geometry
from zcad_core.validation.export_geometry import inspect_export_geometry

from zcad.generators.tolerance_coupon import ToleranceCouponParameters

VOLUME_TOLERANCE_MM3 = 1e-6
SURROUNDING_BAND_MM = 0.2


def coupon_opening_checks(parts, parameters):
    """Intersect full nominal opening prisms with every solid in the main part.

    Check obstruction and a 0.2 mm surrounding band through the plate interval.
    This does not establish global wall thickness, labels, or physical fit.
    """
    p = ToleranceCouponParameters(**parameters)
    p.validate()
    for name, value in vars(p).items():
        values = value if isinstance(value, list) else [value]
        if any(isinstance(v, bool) or not math.isfinite(v) for v in values):
            raise ValueError(f"Nonfinite or invalid coupon parameter: {name}")
    if set(parts) != {"main"}:
        raise ValueError("Coupon opening checks require exactly the main part")
    shape = inspect_export_geometry(parts["main"], "main").shape
    columns = max(len(p.hole_diameters), len(p.slot_widths))
    left = -(columns - 1) * p.cell_width / 2
    checks = []
    for kind, widths, y in (
        ("hole", p.hole_diameters, p.cell_height / 2),
        ("slot", p.slot_widths, -p.cell_height / 2),
    ):
        for index, width in enumerate(widths):
            x = left + index * p.cell_width
            plane = cq.Workplane("XY", origin=(x, y, -p.plate_thickness / 2))
            if kind == "hole":
                profile = plane.circle(width / 2)
            else:
                profile = plane.slot2D(p.cell_height * 0.65, width, 90)
            probe = profile.extrude(p.plate_thickness).val()
            # Sum each solid separately so overlapping stack items cannot hide
            # an obstruction by algebraic cancellation.
            residual = 0.0
            for solid in shape.Solids():
                overlap = solid.intersect(probe)
                volume = overlap.Volume()
                if not overlap.isValid() or not math.isfinite(volume) or volume < 0:
                    raise ValueError("Opening intersection produced invalid evidence")
                residual += volume
            checks.append(
                {
                    "code": "coupon_opening_clearance",
                    "status": "PASS" if residual <= VOLUME_TOLERANCE_MM3 else "FAIL",
                    "message": f"{kind} {index + 1}: opening volume through plate",
                    "part_name": "main",
                    "feature_id": f"{kind}_{index + 1:02d}",
                    "feature_kind": kind,
                    "center_mm": [x, y],
                    "width_mm": width,
                    "length_mm": width if kind == "hole" else p.cell_height * 0.65,
                    "z_interval_mm": [-p.plate_thickness / 2, p.plate_thickness / 2],
                    "method": "solid-intersection-volume",
                    "residual_material_mm3": residual,
                    "volume_tolerance_mm3": VOLUME_TOLERANCE_MM3,
                }
            )
            outer_plane = cq.Workplane("XY", origin=(x, y, -p.plate_thickness / 2))
            if kind == "hole":
                outer_profile = outer_plane.circle(width / 2 + SURROUNDING_BAND_MM)
            else:
                outer_profile = outer_plane.slot2D(
                    p.cell_height * 0.65 + 2 * SURROUNDING_BAND_MM,
                    width + 2 * SURROUNDING_BAND_MM,
                    90,
                )
            band = outer_profile.extrude(p.plate_thickness).val().cut(probe)
            if not band.isValid() or band.Volume() <= 0:
                raise ValueError("Invalid surrounding-material probe")
            # Difference against each solid measures the uncovered union.
            # Duplicate/overlapping solids cannot compensate for missing material.
            missing = band
            for solid in shape.Solids():
                if not missing.Solids():
                    break
                missing = missing.cut(solid)
            missing_volume = missing.Volume()
            if (
                not missing.isValid()
                or not math.isfinite(missing_volume)
                or missing_volume < 0
            ):
                raise ValueError("Material difference produced invalid evidence")
            checks.append(
                {
                    "code": "coupon_surrounding_material",
                    "status": "PASS"
                    if missing_volume <= VOLUME_TOLERANCE_MM3
                    else "FAIL",
                    "message": f"{kind} {index + 1}: surrounding band through plate",
                    "part_name": "main",
                    "feature_id": f"{kind}_{index + 1:02d}",
                    "feature_kind": kind,
                    "center_mm": [x, y],
                    "band_width_mm": SURROUNDING_BAND_MM,
                    "z_interval_mm": [-p.plate_thickness / 2, p.plate_thickness / 2],
                    "method": "sequential-solid-difference-volume",
                    "expected_material_mm3": band.Volume(),
                    "missing_material_mm3": missing_volume,
                    "volume_tolerance_mm3": VOLUME_TOLERANCE_MM3,
                }
            )
    return checks


def feature_checks(*, design_type, parts, parameters):
    """Shared product checks for read-only validation and export snapshots."""
    if design_type != "tolerance_coupon":
        return [
            {
                "code": code,
                "status": "NOT_CHECKED",
                "message": "Only tolerance_coupon has an opening contract",
            }
            for code in ("coupon_opening_clearance", "coupon_surrounding_material")
        ]
    try:
        return coupon_opening_checks(parts, parameters)
    except Exception as error:
        return [
            {
                "code": code,
                "status": "FAIL",
                "message": f"Opening check error: {type(error).__name__}: {error}",
                "part_name": "main",
            }
            for code in ("coupon_opening_clearance", "coupon_surrounding_material")
        ]


def validate_design(**kwargs):
    """Append applicable product evidence before CLI/catalog policy evaluation."""
    report = validate_geometry(**kwargs)
    checks = feature_checks(
        design_type=kwargs["design_type"],
        parts=kwargs["parts"],
        parameters=kwargs.get("parameters") or {},
    )
    report["checks"].extend(checks)
    if any(c["status"] == "FAIL" for c in checks):
        report["evaluated_status"] = "FAIL"
    if kwargs["design_type"] == "tolerance_coupon":
        report["scope"] += (
            "; nominal coupon opening clearance and surrounding material "
            "within declared plate interval"
        )
    return report
