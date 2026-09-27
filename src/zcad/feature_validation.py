"""Product-specific nominal opening checks for read-only design validation."""

import math

import cadquery as cq
from zcad_core.validation.design_report import validate_design as validate_geometry
from zcad_core.validation.export_geometry import inspect_export_geometry

from zcad.generators.tolerance_coupon import ToleranceCouponParameters

VOLUME_TOLERANCE_MM3 = 1e-6


def coupon_opening_checks(parts, parameters):
    """Intersect full nominal opening prisms with every solid in the main part.

    This checks obstruction within the declared plate interval. It does not
    measure opening oversize, wall thickness, labels, or physical fit.
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
    return checks


def validate_design(**kwargs):
    """Append applicable product evidence before CLI/catalog policy evaluation."""
    report = validate_geometry(**kwargs)
    if kwargs["design_type"] != "tolerance_coupon":
        report["checks"].append(
            {
                "code": "coupon_opening_clearance",
                "status": "NOT_CHECKED",
                "message": "Only tolerance_coupon has an opening contract",
            }
        )
        return report
    try:
        checks = coupon_opening_checks(kwargs["parts"], kwargs.get("parameters") or {})
    except Exception as error:
        checks = [
            {
                "code": "coupon_opening_clearance",
                "status": "FAIL",
                "message": f"Opening check error: {type(error).__name__}: {error}",
                "part_name": "main",
            }
        ]
    report["checks"].extend(checks)
    if any(c["status"] == "FAIL" for c in checks):
        report["evaluated_status"] = "FAIL"
    report["scope"] += (
        "; nominal coupon opening clearance within declared plate interval"
    )
    return report
