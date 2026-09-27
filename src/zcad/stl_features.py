"""Sampled coupon feature checks on exported STL bytes, without mesh repair."""

import math

from zcad.generators.tolerance_coupon import ToleranceCouponParameters


def stl_feature_checks(*, design_type, parts, parameters):
    if design_type != "tolerance_coupon":
        return [
            {
                "code": "stl_coupon_features",
                "status": "NOT_CHECKED",
                "message": "Only tolerance_coupon has STL feature probes",
            }
        ]
    p = ToleranceCouponParameters(**parameters)
    p.validate()
    if set(parts) != {"main"}:
        raise ValueError("Coupon STL checks require exactly main")
    left = -(max(len(p.hole_diameters), len(p.slot_widths)) - 1) * p.cell_width / 2
    checks = []
    for kind, widths, y in (
        ("hole", p.hole_diameters, p.cell_height / 2),
        ("slot", p.slot_widths, -p.cell_height / 2),
    ):
        for i, width in enumerate(widths):
            x = left + i * p.cell_width
            radius = width / 2
            half_straight = 0 if kind == "hole" else (p.cell_height * 0.65 - width) / 2
            for label, expected, r in (
                ("opening", False, radius * 0.8),
                ("material", True, radius + 0.1),
            ):
                points = []
                for fraction in (-0.4, 0, 0.4):
                    z = fraction * p.plate_thickness
                    for j in range(16):
                        angle = 2 * math.pi * (j + 0.37) / 16
                        dx, dy = r * math.cos(angle), r * math.sin(angle)
                        dy += math.copysign(half_straight, dy)
                        points.append((x + dx, y + dy, z))
                    if label == "opening":
                        points.append((x, y, z))
                    if half_straight > 0:
                        for side in (-1, 1):
                            for offset in (-0.5, 0, 0.5):
                                points.append(
                                    (x + side * r, y + offset * half_straight, z)
                                )
                failures = [
                    list(point)
                    for point in points
                    if parts["main"].contains(point) != expected
                ]
                checks.append(
                    {
                        "code": f"stl_coupon_{label}_samples",
                        "part_name": "main",
                        "feature_id": f"{kind}_{i + 1:02d}",
                        "status": "FAIL" if failures else "PASS",
                        "message": f"{kind} {i + 1}: sampled {label} occupancy",
                        "method": "ray-parity",
                        "sample_count": len(points),
                        "failed_points_mm": failures,
                        "z_fractions_of_thickness": [-0.4, 0, 0.4],
                        "radial_offset_mm": r - radius,
                        "scope": (
                            "Discrete probes only; unsampled defects "
                            "and exact dimensions unverified"
                        ),
                    }
                )
    return checks
