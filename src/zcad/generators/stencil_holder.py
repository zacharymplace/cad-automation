"""Stencil/transfer paper holder for a tattoo station.

A shallow tray with three different wall heights instead of one
uniform lip: a tall back wall the stack leans against and squares up
on, low side walls that keep it from sliding out sideways, and a very
low front wall -- short enough to pinch a sheet's edge over, with an
open thumb notch cut through it so a fingertip can slip underneath the
whole stack rather than fumbling at a flush edge.

`divider_count` splits the interior into that many extra side-by-side
compartments, for separating precut sheets by client or design instead
of keeping one undivided stack. Each compartment gets its own thumb
notch, sized by `thumb_notch_width`, and -- once there's more than one
-- its own embossed number near the top of the inner back wall, above
where a loaded stack normally reaches, so it stays readable while the
compartment is in use rather than only once it's empty.

This only holds unprinted/blank stencil paper before use -- it never
touches skin, ink, or a used transfer. Like the rest of this line, it
gets wiped down and covered in barrier film along with the station.

A full US-letter sheet (216 x 279 mm) doesn't fit a single print on
this project's default printer profile: 279 mm exceeds the 256 mm
build volume on every axis. The default size here matches a common
precut half-sheet instead; printing a full-letter holder needs either
a larger-format printer or splitting the tray into two joined pieces,
neither of which this generator does today.
"""

from dataclasses import dataclass

import cadquery as cq


@dataclass(frozen=True)
class StencilHolderParameters:
    """Dimensions for the floor and its three wall heights."""

    width: float = 150.0
    depth: float = 210.0
    wall: float = 3.0
    floor_thickness: float = 3.0
    corner_radius: float = 5.0

    back_wall_height: float = 45.0
    side_wall_height: float = 20.0
    front_wall_height: float = 8.0

    thumb_notch: bool = True
    thumb_notch_width: float = 30.0

    divider_count: int = 0
    divider_height: float = 20.0

    compartment_labels: bool = True
    compartment_label_size: float = 5.0
    compartment_label_height: float = 0.3
    # Distance down from the top of the back wall to each number's center.
    compartment_label_margin: float = 10.0

    label: str = "Z$ CAD"
    label_size: float = 3.0
    label_height: float = 0.3

    def compartment_width(self) -> float:
        """Width of each compartment once dividers are accounted for."""
        interior_span = self.width - 2 * self.wall
        return (interior_span - self.divider_count * self.wall) / (
            self.divider_count + 1
        )

    def compartment_centers_x(self) -> list[float]:
        """X center of each compartment, left to right."""
        interior_left = -self.width / 2 + self.wall
        compartment_width = self.compartment_width()

        centers = []
        x = interior_left

        for _ in range(self.divider_count + 1):
            centers.append(x + compartment_width / 2)
            x += compartment_width + self.wall

        return centers

    def divider_centers_x(self) -> list[float]:
        """X center of each divider wall, between compartments."""
        interior_left = -self.width / 2 + self.wall
        compartment_width = self.compartment_width()

        centers = []
        x = interior_left + compartment_width

        for _ in range(self.divider_count):
            centers.append(x + self.wall / 2)
            x += self.wall + compartment_width

        return centers

    def validate(self) -> None:
        positive_values = {
            "width": self.width,
            "depth": self.depth,
            "wall": self.wall,
            "floor_thickness": self.floor_thickness,
            "back_wall_height": self.back_wall_height,
            "side_wall_height": self.side_wall_height,
            "front_wall_height": self.front_wall_height,
            "label_size": self.label_size,
            "label_height": self.label_height,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.corner_radius < 0:
            raise ValueError("corner_radius cannot be negative")

        if not self.label.strip():
            raise ValueError("label cannot be empty")

        if self.width <= 2 * self.wall:
            raise ValueError("width must exceed twice the wall thickness")

        if self.depth <= 2 * self.wall:
            raise ValueError("depth must exceed twice the wall thickness")

        if self.divider_count < 0:
            raise ValueError("divider_count cannot be negative")

        if self.divider_count > 0 and self.divider_height <= 0:
            raise ValueError("divider_height must be greater than zero")

        if self.compartment_width() <= 0:
            raise ValueError("divider_count leaves no room for any compartment")

        if self.thumb_notch:
            if self.thumb_notch_width <= 0:
                raise ValueError("thumb_notch_width must be greater than zero")

            if self.thumb_notch_width > self.compartment_width() - 4:
                raise ValueError(
                    "thumb_notch_width does not fit within one compartment"
                )

        if self.divider_count > 0 and self.compartment_labels:
            if self.compartment_label_size <= 0:
                raise ValueError("compartment_label_size must be greater than zero")

            if self.compartment_label_height <= 0:
                raise ValueError("compartment_label_height must be greater than zero")

            if self.compartment_label_margin < 0:
                raise ValueError("compartment_label_margin cannot be negative")

            if self.compartment_label_size > self.compartment_width() - 4:
                raise ValueError(
                    "compartment_label_size does not fit within one compartment"
                )

            if self.compartment_label_margin < self.compartment_label_size / 2:
                raise ValueError(
                    "compartment_label_margin places the number above the back wall"
                )

            if (
                self.compartment_label_margin
                > self.back_wall_height - self.compartment_label_size / 2
            ):
                raise ValueError(
                    "compartment_label_margin places the number below the floor"
                )


def build_stencil_holder(
    parameters: StencilHolderParameters,
) -> cq.Workplane:
    """Build the floor and its back, side, and front walls."""
    parameters.validate()

    floor = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.floor_thickness,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        floor = floor.edges("|Z").fillet(parameters.corner_radius)

    back_wall = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor_thickness)
        .box(
            parameters.width,
            parameters.wall,
            parameters.back_wall_height,
            centered=(True, False, False),
        )
        .translate((0, parameters.depth / 2 - parameters.wall, 0))
    )

    front_wall = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor_thickness)
        .box(
            parameters.width,
            parameters.wall,
            parameters.front_wall_height,
            centered=(True, False, False),
        )
        .translate((0, -parameters.depth / 2, 0))
    )

    if parameters.thumb_notch:
        for center_x in parameters.compartment_centers_x():
            notch = (
                cq.Workplane("XY")
                .workplane(offset=parameters.floor_thickness - 0.5)
                .box(
                    parameters.thumb_notch_width,
                    parameters.wall + 2,
                    parameters.front_wall_height + 1,
                    centered=(True, True, False),
                )
                .translate((center_x, -parameters.depth / 2 + parameters.wall / 2, 0))
            )
            front_wall = front_wall.cut(notch)

    side_length = parameters.depth - 2 * parameters.wall

    left_wall = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor_thickness)
        .box(
            parameters.wall,
            side_length,
            parameters.side_wall_height,
            centered=(False, True, False),
        )
        .translate((-parameters.width / 2, 0, 0))
    )

    right_wall = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor_thickness)
        .box(
            parameters.wall,
            side_length,
            parameters.side_wall_height,
            centered=(False, True, False),
        )
        .translate((parameters.width / 2 - parameters.wall, 0, 0))
    )

    holder = floor.union(back_wall).union(front_wall).union(left_wall).union(right_wall)

    for center_x in parameters.divider_centers_x():
        divider = (
            cq.Workplane("XY")
            .workplane(offset=parameters.floor_thickness)
            .box(
                parameters.wall,
                side_length,
                parameters.divider_height,
                centered=(True, True, False),
            )
            .translate((center_x, 0, 0))
        )
        holder = holder.union(divider)

    if parameters.divider_count > 0 and parameters.compartment_labels:
        back_inner_y = parameters.depth / 2 - parameters.wall
        label_z = (
            parameters.floor_thickness
            + parameters.back_wall_height
            - parameters.compartment_label_margin
        )

        for index, center_x in enumerate(parameters.compartment_centers_x(), start=1):
            compartment_mark = (
                cq.Workplane("XZ")
                .workplane(offset=-back_inner_y)
                .center(center_x, label_z)
                .text(
                    str(index),
                    parameters.compartment_label_size,
                    parameters.compartment_label_height,
                    halign="center",
                    valign="center",
                )
            )
            holder = holder.union(compartment_mark)

    y_back_face = parameters.depth / 2

    mark = (
        cq.Workplane("XZ")
        .workplane(offset=-(y_back_face + parameters.label_height))
        .center(0, parameters.floor_thickness + parameters.back_wall_height / 2)
        .text(
            parameters.label,
            parameters.label_size,
            parameters.label_height,
            halign="center",
            valign="center",
        )
    )

    return holder.union(mark)
