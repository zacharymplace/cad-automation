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
            for label, r in (
                ("opening", radius * 0.8),
                ("material", radius + 0.1),
            ):
                if label == "opening":
                    xy = []
                    for j in range(16):
                        angle = 2 * math.pi * (j + 0.37) / 16
                        dx, dy = r * math.cos(angle), r * math.sin(angle)
                        xy.append((x + dx, y + dy + math.copysign(half_straight, dy)))
                    xy.append((x, y))
                    if half_straight > 0:
                        xy.extend(
                            (x + side * r, y + offset * half_straight)
                            for side in (-1, 1)
                            for offset in (-0.5, 0, 0.5)
                        )
                    probes = [
                        {
                            "xy_mm": list(point),
                            **parts["main"].vertical_clearance(
                                *point, -p.plate_thickness / 2, p.plate_thickness / 2
                            ),
                        }
                        for point in xy
                    ]
                    checks.append(
                        {
                            "code": "stl_coupon_opening_vertical_clearance",
                            "part_name": "main",
                            "feature_id": f"{kind}_{i + 1:02d}",
                            "status": "PASS"
                            if all(probe["clear"] for probe in probes)
                            else "FAIL",
                            "message": (
                                f"{kind} {i + 1}: full-depth clearance at sampled XY"
                            ),
                            "method": "vertical-segment-surface-contact-and-occupancy",
                            "sample_count": len(probes),
                            "probes": probes,
                            "z_interval_mm": [
                                -p.plate_thickness / 2,
                                p.plate_thickness / 2,
                            ],
                            "radial_offset_mm": r - radius,
                            "scope": (
                                "Continuous Z at discrete XY; lateral gaps between "
                                "probes and exact opening dimensions unverified"
                            ),
                        }
                    )
                    continue
                xy = []
                for j in range(16):
                    angle = 2 * math.pi * (j + 0.37) / 16
                    dx, dy = r * math.cos(angle), r * math.sin(angle)
                    xy.append((x + dx, y + dy + math.copysign(half_straight, dy)))
                if half_straight > 0:
                    xy.extend(
                        (x + side * r, y + offset * half_straight)
                        for side in (-1, 1)
                        for offset in (-0.5, 0, 0.5)
                    )
                probes = [
                    {
                        "xy_mm": list(point),
                        **parts["main"].vertical_material(
                            *point, -p.plate_thickness / 2, p.plate_thickness / 2
                        ),
                    }
                    for point in xy
                ]
                checks.append(
                    {
                        "code": "stl_coupon_material_vertical_coverage",
                        "part_name": "main",
                        "feature_id": f"{kind}_{i + 1:02d}",
                        "status": "PASS"
                        if all(p["covered"] for p in probes)
                        else "FAIL",
                        "message": f"{kind} {i + 1}: full-depth material at sampled XY",
                        "method": "vertical-interior-surface-contact-and-occupancy",
                        "sample_count": len(probes),
                        "probes": probes,
                        "z_interval_mm": [
                            -p.plate_thickness / 2,
                            p.plate_thickness / 2,
                        ],
                        "radial_offset_mm": r - radius,
                        "scope": (
                            "Continuous Z excluding endpoint tolerance bands; "
                            "lateral gaps between probes and wall thickness unverified"
                        ),
                    }
                )
    return checks
