"""Continuous vertical sweeps for the garden module's vertical extrusions."""

import math

import cadquery as cq

TOLERANCE_MM3 = 1e-6


def vertical_sweep(module: cq.Shape, lift: float) -> cq.Shape:
    """Sweep this module's horizontal faces upward, retaining the original solid.

    Specialized to the garden geometry: horizontal caps and vertical walls,
    including vertical corner fillets. Not a general curved-motion sweep.
    """
    if not math.isfinite(lift) or lift <= 0:
        raise ValueError("Insertion lift must be positive and finite")
    prisms = []
    for face in module.Faces():
        if face.geomType() == "PLANE" and abs(face.normalAt().z) > 1 - 1e-9:
            prisms.append(
                cq.Solid.extrudeLinear(
                    face.outerWire(), face.innerWires(), cq.Vector(0, 0, lift)
                )
            )
    if not prisms:
        raise ValueError("No horizontal faces available for garden sweep")
    sweep = module.fuse(*prisms).clean()
    if not sweep.isValid() or not math.isfinite(sweep.Volume()):
        raise ValueError("Invalid insertion sweep")
    return sweep


def insertion_plan(module: cq.Shape, instances: list[dict]) -> dict:
    """Find an order using directed swept-volume blocking constraints.

    If B intersects A's sweep, A must precede B. A cycle means no order
    exists under fixed XY, top-down, one-module-at-a-time insertion.
    """
    levels = [i["position_mm"][2] for i in instances]
    lift = module.BoundingBox().zlen + max(levels) - min(levels) + 1.0
    sweep = vertical_sweep(module, lift)
    solids = [module.translate(tuple(i["position_mm"])) for i in instances]
    prerequisites = {i["name"]: set() for i in instances}
    blocked = []
    for i, instance in enumerate(instances):
        moving = sweep.translate(tuple(instance["position_mm"]))
        a = moving.BoundingBox()
        for j, obstacle in enumerate(solids):
            if i == j:
                continue
            b = obstacle.BoundingBox()
            if any(
                getattr(a, axis + "max") <= getattr(b, axis + "min")
                or getattr(b, axis + "max") <= getattr(a, axis + "min")
                for axis in "xyz"
            ):
                continue
            volume = moving.intersect(obstacle).Volume()
            if not math.isfinite(volume):
                raise ValueError("Nonfinite insertion intersection")
            if volume > TOLERANCE_MM3:
                other = instances[j]["name"]
                prerequisites[other].add(instance["name"])
                blocked.append(
                    {
                        "moving": instance["name"],
                        "blocked_by": other,
                        "swept_overlap_mm3": volume,
                    }
                )
    order = []
    remaining = set(prerequisites)
    while remaining:
        available = sorted(n for n in remaining if not prerequisites[n] & remaining)
        if not available:
            break
        selected = available[0]
        order.append(selected)
        remaining.remove(selected)
    return {
        "status": "BLOCKED" if remaining else "PASS",
        "method": "continuous-horizontal-face-sweep",
        "motion": "fixed XY; lower from +Z; no rotation",
        "lift_mm": lift,
        "volume_tolerance_mm3": TOLERANCE_MM3,
        "assembly_order": order if not remaining else [],
        "partial_order": order if remaining else [],
        "unresolved": sorted(remaining),
        "blocked_moves": blocked,
        "scope": (
            "Nominal module geometry; tools, hands, deformation and friction excluded"
        ),
    }
