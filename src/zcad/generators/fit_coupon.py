"""Peg-and-socket fit calibration coupon."""

from dataclasses import dataclass

import cadquery as cq


@dataclass(frozen=True)
class FitCouponParameters:
    """Parameters for matching peg and socket fit tests."""

    nominal_diameter: float
    clearances: list[float]
    plate_thickness: float = 5.0
    peg_height: float = 10.0
    cell_width: float = 20.0
    margin: float = 5.0
    corner_radius: float = 3.0

    def validate(self) -> None:
        if self.nominal_diameter <= 0:
            raise ValueError("nominal_diameter must be greater than zero")

        if not self.clearances:
            raise ValueError("clearances cannot be empty")

        if len(set(self.clearances)) != len(self.clearances):
            raise ValueError("clearances must be unique")

        for clearance in self.clearances:
            if clearance < 0:
                raise ValueError("clearances cannot be negative")

        for name in (
            "plate_thickness",
            "peg_height",
            "cell_width",
            "margin",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be greater than zero")

        largest_socket = self.nominal_diameter + max(self.clearances)

        if largest_socket >= self.cell_width:
            raise ValueError("socket diameter must be smaller than cell_width")

        if self.corner_radius < 0:
            raise ValueError("corner_radius cannot be negative")


def build_fit_coupon(
    parameters: FitCouponParameters,
) -> cq.Workplane:
    """Build connected peg and socket calibration strips."""
    parameters.validate()

    count = len(parameters.clearances)

    strip_width = 2 * parameters.margin + count * parameters.cell_width
    strip_depth = 2 * parameters.margin + parameters.cell_width

    gap = 6.0
    total_depth = strip_depth * 2 + gap

    socket_y = total_depth / 2 - strip_depth / 2
    peg_y = -total_depth / 2 + strip_depth / 2

    socket_strip = (
        cq.Workplane("XY")
        .center(0, socket_y)
        .box(
            strip_width,
            strip_depth,
            parameters.plate_thickness,
        )
    )

    peg_strip = (
        cq.Workplane("XY")
        .center(0, peg_y)
        .box(
            strip_width,
            strip_depth,
            parameters.plate_thickness,
        )
    )

    if parameters.corner_radius > 0:
        socket_strip = socket_strip.edges("|Z").fillet(parameters.corner_radius)
        peg_strip = peg_strip.edges("|Z").fillet(parameters.corner_radius)

    left_x = -strip_width / 2 + parameters.margin + parameters.cell_width / 2

    for index, clearance in enumerate(parameters.clearances):
        x_position = left_x + index * parameters.cell_width

        socket_diameter = parameters.nominal_diameter + clearance

        socket_strip = (
            socket_strip.faces(">Z")
            .workplane()
            .pushPoints([(x_position, socket_y)])
            .hole(socket_diameter)
        )

        peg = (
            cq.Workplane("XY")
            .workplane(offset=parameters.plate_thickness / 2)
            .center(
                x_position,
                peg_y,
            )
            .circle(parameters.nominal_diameter / 2)
            .extrude(parameters.peg_height)
        )

        peg_strip = peg_strip.union(peg)

    bridge_width = 8.0

    bridge = cq.Workplane("XY").box(
        bridge_width,
        gap,
        parameters.plate_thickness,
    )

    return socket_strip.union(peg_strip).union(bridge)
