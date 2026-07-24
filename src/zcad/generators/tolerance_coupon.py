"""Printer tolerance calibration coupon."""

from dataclasses import dataclass

import cadquery as cq


@dataclass(frozen=True)
class ToleranceCouponParameters:
    """Dimensions for a hole and slot calibration coupon."""

    hole_diameters: list[float]
    slot_widths: list[float]
    plate_thickness: float = 4.0
    cell_width: float = 18.0
    cell_height: float = 18.0
    margin: float = 5.0
    corner_radius: float = 3.0

    def validate(self) -> None:
        if not self.hole_diameters:
            raise ValueError("hole_diameters cannot be empty")

        if not self.slot_widths:
            raise ValueError("slot_widths cannot be empty")

        for name, values in {
            "hole_diameters": self.hole_diameters,
            "slot_widths": self.slot_widths,
        }.items():
            for value in values:
                if value <= 0:
                    raise ValueError(f"{name} values must be greater than zero")

        for name in (
            "plate_thickness",
            "cell_width",
            "cell_height",
            "margin",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.corner_radius < 0:
            raise ValueError("corner_radius cannot be negative")

        largest_feature = max(
            max(self.hole_diameters),
            max(self.slot_widths),
        )

        if largest_feature >= min(
            self.cell_width,
            self.cell_height,
        ):
            raise ValueError("Calibration features must be smaller than their cells")


def build_tolerance_coupon(
    parameters: ToleranceCouponParameters,
) -> cq.Workplane:
    """Build a two-row tolerance coupon."""
    parameters.validate()

    column_count = max(
        len(parameters.hole_diameters),
        len(parameters.slot_widths),
    )

    plate_width = 2 * parameters.margin + column_count * parameters.cell_width
    plate_depth = 2 * parameters.margin + 2 * parameters.cell_height

    model = cq.Workplane("XY").box(
        plate_width,
        plate_depth,
        parameters.plate_thickness,
    )

    if parameters.corner_radius > 0:
        model = model.edges("|Z").fillet(parameters.corner_radius)

    left_edge = -plate_width / 2 + parameters.margin + parameters.cell_width / 2

    upper_y = parameters.cell_height / 2
    lower_y = -parameters.cell_height / 2

    for index, diameter in enumerate(parameters.hole_diameters):
        x_position = left_edge + index * parameters.cell_width

        model = (
            model.faces(">Z")
            .workplane()
            .pushPoints([(x_position, upper_y)])
            .hole(diameter)
        )

    slot_length = parameters.cell_height * 0.65

    for index, slot_width in enumerate(parameters.slot_widths):
        x_position = left_edge + index * parameters.cell_width

        slot = (
            cq.Workplane("XY")
            .center(x_position, lower_y)
            .slot2D(
                slot_length,
                slot_width,
                angle=90,
            )
            .extrude(parameters.plate_thickness * 2)
        )

        model = model.cut(slot)

    return model
