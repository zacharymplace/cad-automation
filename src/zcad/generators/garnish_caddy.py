"""Garnish caddy for a home bar station: separate compartments for
citrus wedges, cherries, olives, and mint instead of one shared bowl.

`compartment_count` splits the interior into that many equal
compartments along the caddy's length, the same divider math
`stencil_holder` uses for its own compartments. Pass `compartment_widths`
to size them individually instead -- a wider slot for lime wedges next to
narrower ones for olives and cherry stems, say -- as long as they sum to
the same interior span the equal-division default would have used. Each
compartment gets an embossed number once there's more than one, so a
particular garnish can be assigned a spot consistently across sessions.

A thumb notch cut through one end wall -- the same technique
`stencil_holder` uses for its own front wall -- makes the caddy easier
to lift and carry to and from a cart or table.

Like the rest of this line's design philosophy, garnishes sit above
juice or brine they shed, not soaking in it -- but this is a shallow
open caddy, not a basin: expect to wipe it out between uses rather
than rely on any built-in drainage.

Food-safety scope: unlike every product in the tattoo line, this one
holds food directly against the printed surface. FDM prints -- PETG
included -- have layer-line porosity that's hard to fully sanitize, so
this is meant for short-session serving that gets washed promptly
after each use, not for storing garnishes loaded for hours or days.
It is not a substitute for food-service-rated dishware, and printing
it in a food-safe-labeled filament does not by itself make the printed
part food-safe -- that labeling describes the raw material, not a
part with exposed layer lines. A food-safe two-part epoxy coating (the
kind used to finish charcuterie boards) can seal those layer lines for
longer or repeated food contact, if that's worth doing for your use.
"""

from dataclasses import dataclass

import cadquery as cq


@dataclass(frozen=True)
class GarnishCaddyParameters:
    """Dimensions for the caddy shell and its compartments."""

    width: float = 220.0
    depth: float = 80.0
    wall: float = 3.0
    floor_thickness: float = 3.0
    wall_height: float = 35.0
    corner_radius: float = 6.0

    compartment_count: int = 4
    compartment_widths: tuple[float, ...] = ()

    compartment_labels: bool = True
    compartment_label_size: float = 8.0
    compartment_label_height: float = 0.3

    thumb_notch: bool = True
    thumb_notch_width: float = 25.0

    label: str = "Z$ CAD"
    label_size: float = 5.0
    label_height: float = 0.4

    def compartment_width(self) -> float:
        """Width of each compartment under equal division (the default)."""
        interior_width = self.width - 2 * self.wall
        return (
            interior_width - (self.compartment_count - 1) * self.wall
        ) / self.compartment_count

    def compartment_widths_list(self) -> list[float]:
        """Per-compartment widths, left to right."""
        if self.compartment_widths:
            return list(self.compartment_widths)
        return [self.compartment_width()] * self.compartment_count

    def compartment_centers_x(self) -> list[float]:
        """X center of each compartment, left to right."""
        interior_left = -self.width / 2 + self.wall

        centers = []
        x = interior_left

        for compartment_width in self.compartment_widths_list():
            centers.append(x + compartment_width / 2)
            x += compartment_width + self.wall

        return centers

    def divider_centers_x(self) -> list[float]:
        """X center of each divider wall, between compartments."""
        interior_left = -self.width / 2 + self.wall
        widths = self.compartment_widths_list()

        centers = []
        x = interior_left

        for compartment_width in widths[:-1]:
            x += compartment_width
            centers.append(x + self.wall / 2)
            x += self.wall

        return centers

    def validate(self) -> None:
        positive_values = {
            "width": self.width,
            "depth": self.depth,
            "wall": self.wall,
            "floor_thickness": self.floor_thickness,
            "wall_height": self.wall_height,
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

        if self.compartment_count < 1:
            raise ValueError("compartment_count must be at least one")

        if self.compartment_widths:
            if len(self.compartment_widths) != self.compartment_count:
                raise ValueError(
                    "compartment_widths must have one entry per compartment_count"
                )

            if any(w <= 0 for w in self.compartment_widths):
                raise ValueError("compartment_widths must all be greater than zero")

            interior_width = self.width - 2 * self.wall
            widths_span = (
                sum(self.compartment_widths) + (self.compartment_count - 1) * self.wall
            )

            if abs(widths_span - interior_width) > 1e-6:
                raise ValueError(
                    "compartment_widths plus dividers must add up to the interior width"
                )
        elif self.compartment_width() <= 0:
            raise ValueError("compartment_count leaves no room for any compartment")

        if self.thumb_notch:
            if self.thumb_notch_width <= 0:
                raise ValueError("thumb_notch_width must be greater than zero")

            if self.thumb_notch_width > self.depth - 2 * self.wall - 4:
                raise ValueError("thumb_notch_width does not fit within the end wall")

        if self.compartment_count > 1 and self.compartment_labels:
            if self.compartment_label_size <= 0:
                raise ValueError("compartment_label_size must be greater than zero")

            if self.compartment_label_height <= 0:
                raise ValueError("compartment_label_height must be greater than zero")

            if self.compartment_label_size > min(self.compartment_widths_list()) - 4:
                raise ValueError(
                    "compartment_label_size does not fit within one compartment"
                )

            if self.compartment_label_size > self.depth - 2 * self.wall - 4:
                raise ValueError(
                    "compartment_label_size does not fit within the caddy depth"
                )


def build_garnish_caddy(
    parameters: GarnishCaddyParameters,
) -> cq.Workplane:
    """Build the caddy shell, its dividers, and the thumb notch."""
    parameters.validate()

    outer = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.floor_thickness + parameters.wall_height,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        outer = outer.edges("|Z").fillet(parameters.corner_radius)

    inner = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor_thickness)
        .box(
            parameters.width - 2 * parameters.wall,
            parameters.depth - 2 * parameters.wall,
            parameters.wall_height,
            centered=(True, True, False),
        )
    )

    caddy = outer.cut(inner)

    for center_x in parameters.divider_centers_x():
        divider = (
            cq.Workplane("XY")
            .workplane(offset=parameters.floor_thickness)
            .center(center_x, 0)
            .box(
                parameters.wall,
                parameters.depth - 2 * parameters.wall,
                parameters.wall_height,
                centered=(True, True, False),
            )
        )
        caddy = caddy.union(divider)

    if parameters.thumb_notch:
        notch_center_x = -parameters.width / 2 + parameters.wall / 2
        notch = (
            cq.Workplane("XY")
            .workplane(offset=parameters.floor_thickness - 0.5)
            .center(notch_center_x, 0)
            .box(
                parameters.wall + 2,
                parameters.thumb_notch_width,
                parameters.wall_height + 1,
                centered=(True, True, False),
            )
        )
        caddy = caddy.cut(notch)

    if parameters.compartment_count > 1 and parameters.compartment_labels:
        for index, center_x in enumerate(parameters.compartment_centers_x(), start=1):
            mark = (
                cq.Workplane("XY")
                .workplane(offset=parameters.floor_thickness)
                .center(center_x, 0)
                .text(
                    str(index),
                    parameters.compartment_label_size,
                    parameters.compartment_label_height,
                    halign="center",
                    valign="center",
                )
            )
            caddy = caddy.union(mark)

    y_back_face = parameters.depth / 2

    mark = (
        cq.Workplane("XZ")
        .workplane(offset=-(y_back_face + parameters.label_height))
        .center(0, parameters.floor_thickness + parameters.wall_height * 0.2)
        .text(
            parameters.label,
            parameters.label_size,
            parameters.label_height,
            halign="center",
            valign="center",
        )
    )

    return caddy.union(mark)
