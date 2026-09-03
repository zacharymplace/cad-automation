"""Tattoo machine grip stand: a two-point cradle that keeps a machine
off the counter between passes.

Most of a tattoo machine's length is either the needle bar and tip
(sterile field, must never touch a printed surface) or the coils/motor
(irregular, hard to cradle generically). What every machine -- coil or
rotary -- shares is a roughly cylindrical grip section. This stand
supports only that: two U-shaped notches, spaced along the grip's
length, cut into raised blocks on a flat base. The machine rests
across both notches by its grip alone; the tip end simply extends
forward past the front notch, unsupported and untouched.

`machine_count` gangs multiple side-by-side cradle lanes onto one
base, for the stations that keep several machines loaded and swap
between them mid-session rather than running just one at a time.

Like every other clean-zone accessory here, this never contacts the
tip or the client -- it gets wiped down and covered in barrier film
like the rest of the station.
"""

from dataclasses import dataclass

import cadquery as cq


@dataclass(frozen=True)
class GripStandParameters:
    """Dimensions for the base and its two grip-cradling notches."""

    base_width: float = 60.0
    base_depth: float = 95.0
    base_height: float = 6.0
    corner_radius: float = 4.0

    grip_diameter: float = 25.0
    grip_hole_clearance: float = 1.0

    ridge_height: float = 20.0
    ridge_block_width: float = 40.0
    ridge_block_length: float = 16.0
    notch_spacing: float = 55.0
    notch_side_wall: float = 4.0
    notch_wall_min: float = 2.0
    base_edge_margin: float = 8.0

    machine_count: int = 1
    machine_pitch: float = 50.0

    label: str = "Z$ CAD"
    label_size: float = 3.0
    label_height: float = 0.3

    @property
    def grip_hole_diameter(self) -> float:
        return self.grip_diameter + self.grip_hole_clearance

    def notch_centers_y(self) -> tuple[float, float]:
        """Y position of each notch block's center, front and back."""
        return (-self.notch_spacing / 2, self.notch_spacing / 2)

    def lane_centers_x(self) -> list[float]:
        """X position of each machine lane's center, evenly spaced and
        centered on the base."""
        if self.machine_count < 2:
            return [0.0]

        start = -(self.machine_count - 1) * self.machine_pitch / 2
        return [
            start + index * self.machine_pitch for index in range(self.machine_count)
        ]

    def lanes_span(self) -> float:
        """Total X extent from the leftmost lane's outer edge to the
        rightmost lane's outer edge."""
        return (self.machine_count - 1) * self.machine_pitch + self.ridge_block_width

    def validate(self) -> None:
        positive_values = {
            "base_width": self.base_width,
            "base_depth": self.base_depth,
            "base_height": self.base_height,
            "grip_diameter": self.grip_diameter,
            "ridge_height": self.ridge_height,
            "ridge_block_width": self.ridge_block_width,
            "ridge_block_length": self.ridge_block_length,
            "notch_spacing": self.notch_spacing,
            "notch_side_wall": self.notch_side_wall,
            "notch_wall_min": self.notch_wall_min,
            "label_size": self.label_size,
            "label_height": self.label_height,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.corner_radius < 0:
            raise ValueError("corner_radius cannot be negative")

        if self.grip_hole_clearance < 0:
            raise ValueError("grip_hole_clearance cannot be negative")

        if self.base_edge_margin < 0:
            raise ValueError("base_edge_margin cannot be negative")

        if not self.label.strip():
            raise ValueError("label cannot be empty")

        if self.notch_spacing <= self.ridge_block_length:
            raise ValueError("notch_spacing must exceed ridge_block_length")

        if self.ridge_block_width <= self.grip_hole_diameter + 2 * self.notch_side_wall:
            raise ValueError(
                "ridge_block_width must exceed grip_hole_diameter plus side walls"
            )

        if self.machine_count < 1:
            raise ValueError("machine_count must be at least one")

        if self.machine_count > 1:
            if self.machine_pitch <= self.ridge_block_width:
                raise ValueError("machine_pitch must exceed ridge_block_width")

        required_width = self.lanes_span() + 2 * self.base_edge_margin

        if self.base_width < required_width:
            raise ValueError(
                "base_width is too small for machine_count and machine_pitch"
            )

        required_depth = (
            self.notch_spacing + self.ridge_block_length + 2 * self.base_edge_margin
        )

        if self.base_depth < required_depth:
            raise ValueError(
                "base_depth is too small for notch_spacing and base_edge_margin"
            )

        if self.ridge_height < self.grip_hole_diameter / 2 + self.notch_wall_min:
            raise ValueError(
                "ridge_height must clear grip_hole_diameter plus notch_wall_min"
            )


def _notch_block(
    parameters: GripStandParameters,
    center_x: float,
    center_y: float,
) -> cq.Workplane:
    """One raised block with a half-cylinder notch cradling the grip."""
    block = (
        cq.Workplane("XY")
        .workplane(offset=parameters.base_height)
        .center(center_x, center_y)
        .rect(parameters.ridge_block_width, parameters.ridge_block_length)
        .extrude(parameters.ridge_height)
    )

    grip_radius = parameters.grip_hole_diameter / 2
    groove_z = parameters.base_height + parameters.ridge_height

    margin = 1.0
    y0 = center_y - parameters.ridge_block_length / 2 - margin
    y1 = center_y + parameters.ridge_block_length / 2 + margin

    groove = (
        cq.Workplane("XZ")
        .workplane(offset=-y0)
        .center(center_x, groove_z)
        .circle(grip_radius)
        .extrude(-(y1 - y0))
    )

    return block.cut(groove)


def build_grip_stand(
    parameters: GripStandParameters,
) -> cq.Workplane:
    """Build the base and its two grip-cradling notch blocks."""
    parameters.validate()

    stand = cq.Workplane("XY").box(
        parameters.base_width,
        parameters.base_depth,
        parameters.base_height,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        stand = stand.edges("|Z").fillet(parameters.corner_radius)

    for center_x in parameters.lane_centers_x():
        for center_y in parameters.notch_centers_y():
            stand = stand.union(_notch_block(parameters, center_x, center_y))

    y_front_face = -parameters.base_depth / 2

    mark = (
        cq.Workplane("XZ")
        .workplane(offset=-y_front_face)
        .center(0, parameters.base_height / 2)
        .text(
            parameters.label,
            parameters.label_size,
            parameters.label_height,
            halign="center",
            valign="center",
        )
    )

    return stand.union(mark)
