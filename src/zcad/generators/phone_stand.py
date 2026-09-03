"""Adjustable phone/tablet stand with a printed friction hinge.

Three parts: a `base` foot with a device slot near its front edge, a
`cradle` back-rest the device leans against, and a `pin` that passes
through both parts' interleaved hinge knuckles. The base and cradle
knuckles alternate along a shared X axis (piano-hinge style); once
assembled with the pin, friction between the pin and the knuckle bores
holds whatever tilt angle the cradle is left at -- there is no separate
locking feature, so the hold comes entirely from that fit. Because the
right amount of friction depends on the printer and material, dial it
in with `fit_coupon` or `tolerance_coupon` before committing to a full
print: `pin_hole_diameter - pin_diameter` is the controlling clearance.
"""

from dataclasses import dataclass

import cadquery as cq

ModelParts = dict[str, cq.Workplane]

HingeSegment = tuple[float, float, str]


@dataclass(frozen=True)
class PhoneStandParameters:
    """Dimensions for the base, cradle, and hinge pin."""

    device_width: float
    device_thickness: float

    base_width: float = 90.0
    base_depth: float = 70.0
    base_wall: float = 4.0

    slot_offset: float = 40.0
    slot_wall: float = 3.0
    slot_height: float = 10.0
    slot_clearance: float = 2.0

    cradle_width: float = 90.0
    cradle_height: float = 70.0
    cradle_wall: float = 4.0

    corner_radius: float = 3.0

    knuckle_count: int = 5
    knuckle_diameter: float = 10.0
    knuckle_length: float = 12.0
    knuckle_gap: float = 0.6

    pin_hole_diameter: float = 4.0
    pin_diameter: float = 4.2
    pin_margin: float = 3.0

    @property
    def knuckle_radius(self) -> float:
        return self.knuckle_diameter / 2

    @property
    def slot_width(self) -> float:
        """Gap between the two slot walls that the device edge sits in."""
        return self.device_thickness + self.slot_clearance

    def hinge_segments(self) -> tuple[HingeSegment, ...]:
        """Knuckle segments along the shared hinge X axis, alternating
        `"base"` and `"cradle"` starting and ending on `"base"`."""
        total = self.total_hinge_width()
        start = -total / 2

        segments = []

        for index in range(self.knuckle_count):
            segment_start = start + index * (self.knuckle_length + self.knuckle_gap)
            segment_end = segment_start + self.knuckle_length
            owner = "base" if index % 2 == 0 else "cradle"
            segments.append((segment_start, segment_end, owner))

        return tuple(segments)

    def total_hinge_width(self) -> float:
        return (
            self.knuckle_count * self.knuckle_length
            + (self.knuckle_count - 1) * self.knuckle_gap
        )

    def pin_length(self) -> float:
        return self.total_hinge_width() + 2 * self.pin_margin

    def validate(self) -> None:
        positive_values = {
            "device_width": self.device_width,
            "device_thickness": self.device_thickness,
            "base_width": self.base_width,
            "base_depth": self.base_depth,
            "base_wall": self.base_wall,
            "slot_wall": self.slot_wall,
            "slot_height": self.slot_height,
            "cradle_width": self.cradle_width,
            "cradle_height": self.cradle_height,
            "cradle_wall": self.cradle_wall,
            "knuckle_diameter": self.knuckle_diameter,
            "knuckle_length": self.knuckle_length,
            "pin_hole_diameter": self.pin_hole_diameter,
            "pin_diameter": self.pin_diameter,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        for name, value in {
            "slot_offset": self.slot_offset,
            "slot_clearance": self.slot_clearance,
            "corner_radius": self.corner_radius,
            "knuckle_gap": self.knuckle_gap,
            "pin_margin": self.pin_margin,
        }.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

        if self.knuckle_count < 3 or self.knuckle_count % 2 == 0:
            raise ValueError("knuckle_count must be an odd number of at least 3")

        wall_around_pin = self.knuckle_diameter - self.pin_hole_diameter
        if wall_around_pin < 2.0:
            raise ValueError(
                "knuckle_diameter must exceed pin_hole_diameter by at least 2mm"
            )

        clearance = self.pin_hole_diameter - self.pin_diameter
        if not (-0.3 <= clearance <= 0.6):
            raise ValueError(
                "pin_hole_diameter - pin_diameter "
                f"({clearance:.2f}mm) is outside the friction-fit band "
                "(-0.3mm to 0.6mm); calibrate with fit_coupon first"
            )

        total_hinge_width = self.total_hinge_width()

        if total_hinge_width >= self.base_width:
            raise ValueError("hinge knuckles do not fit within base_width")

        if total_hinge_width >= self.cradle_width:
            raise ValueError("hinge knuckles do not fit within cradle_width")

        if self.device_width >= self.base_width:
            raise ValueError("device_width does not fit within base_width")

        if self.device_width >= self.cradle_width:
            raise ValueError("device_width does not fit within cradle_width")

        if self.slot_offset < self.knuckle_radius + 2.0:
            raise ValueError("slot_offset is too close to the hinge knuckles")

        slot_far_edge = (
            self.slot_offset + self.slot_wall + self.slot_width + self.slot_wall
        )

        if slot_far_edge >= self.base_depth:
            raise ValueError("device slot does not fit within base_depth")


def _knuckle_solid(
    *,
    segment: HingeSegment,
    plate_top_z: float,
    radius: float,
) -> cq.Workplane:
    """One hinge knuckle: a cylinder on the shared axis, fused to a
    pedestal that reaches the plate's top face for a clean union."""
    segment_start, segment_end, _owner = segment
    segment_length = segment_end - segment_start
    segment_mid = (segment_start + segment_end) / 2
    axis_z = plate_top_z + radius

    cylinder = (
        cq.Workplane("YZ")
        .workplane(offset=segment_start)
        .center(0, axis_z)
        .circle(radius)
        .extrude(segment_length)
    )

    pedestal = (
        cq.Workplane("XY")
        .box(
            segment_length,
            radius,
            axis_z - plate_top_z,
            centered=(True, False, False),
        )
        .translate((segment_mid, 0.0, plate_top_z))
    )

    return cylinder.union(pedestal)


def _add_hinge_knuckles(
    plate: cq.Workplane,
    *,
    parameters: PhoneStandParameters,
    plate_top_z: float,
    owner: str,
) -> cq.Workplane:
    """Fuse this owner's knuckles onto `plate` and bore the shared pin
    hole through all of them."""
    segments = [
        segment for segment in parameters.hinge_segments() if segment[2] == owner
    ]

    for segment in segments:
        plate = plate.union(
            _knuckle_solid(
                segment=segment,
                plate_top_z=plate_top_z,
                radius=parameters.knuckle_radius,
            )
        )

    total = parameters.total_hinge_width()
    bore_margin = 1.0
    axis_z = plate_top_z + parameters.knuckle_radius

    bore = (
        cq.Workplane("YZ")
        .workplane(offset=-total / 2 - bore_margin)
        .center(0, axis_z)
        .circle(parameters.pin_hole_diameter / 2)
        .extrude(total + 2 * bore_margin)
    )

    return plate.cut(bore)


def build_base(
    parameters: PhoneStandParameters,
) -> cq.Workplane:
    """Build the foot: a flat plate with a device slot and hinge
    knuckles rising from its back (Y=0) edge."""
    plate = cq.Workplane("XY").box(
        parameters.base_width,
        parameters.base_depth,
        parameters.base_wall,
        centered=(True, False, False),
    )

    if parameters.corner_radius > 0:
        plate = plate.edges("|Z").fillet(parameters.corner_radius)

    near_wall_start = parameters.slot_offset
    near_wall_end = near_wall_start + parameters.slot_wall
    far_wall_start = near_wall_end + parameters.slot_width
    far_wall_end = far_wall_start + parameters.slot_wall

    for wall_start, wall_end in (
        (near_wall_start, near_wall_end),
        (far_wall_start, far_wall_end),
    ):
        wall = (
            cq.Workplane("XY")
            .workplane(offset=parameters.base_wall)
            .box(
                parameters.base_width,
                wall_end - wall_start,
                parameters.slot_height,
                centered=(True, False, False),
            )
            .translate((0.0, wall_start, 0.0))
        )
        plate = plate.union(wall)

    return _add_hinge_knuckles(
        plate,
        parameters=parameters,
        plate_top_z=parameters.base_wall,
        owner="base",
    )


def build_cradle(
    parameters: PhoneStandParameters,
) -> cq.Workplane:
    """Build the cradle: a flat back-rest with hinge knuckles rising
    from its bottom (Y=0) edge."""
    plate = cq.Workplane("XY").box(
        parameters.cradle_width,
        parameters.cradle_height,
        parameters.cradle_wall,
        centered=(True, False, False),
    )

    if parameters.corner_radius > 0:
        plate = plate.edges("|Z").fillet(parameters.corner_radius)

    return _add_hinge_knuckles(
        plate,
        parameters=parameters,
        plate_top_z=parameters.cradle_wall,
        owner="cradle",
    )


def build_pin(
    parameters: PhoneStandParameters,
) -> cq.Workplane:
    """Build the hinge pin: a plain rod sized to friction-fit the
    knuckle bores."""
    length = parameters.pin_length()

    return (
        cq.Workplane("YZ")
        .workplane(offset=-length / 2)
        .circle(parameters.pin_diameter / 2)
        .extrude(length)
    )


def build_phone_stand(
    parameters: PhoneStandParameters,
) -> ModelParts:
    """Build the base, cradle, and pin."""
    parameters.validate()

    return {
        "base": build_base(parameters),
        "cradle": build_cradle(parameters),
        "pin": build_pin(parameters),
    }
