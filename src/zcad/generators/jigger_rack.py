"""Jigger rack for a home bar station: a raised plate that holds a row
of jiggers upside down over a base, instead of leaving them loose on the
bar top where they roll and collect spilled residue.

A jigger's cone shape self-centers against a plain circular hole, so
the rack plate needs nothing fancier than a row of round through-holes
-- no frustum or loft geometry to match a specific jigger's taper. Each
hole gets an optional conical countersink at its mouth
(`jigger_hole_chamfer`), the same technique `ink_cap_tray` uses for its
cap holes, so a jigger drops in or lifts out without fumbling for the
exact opening.

Four cylindrical legs (`leg_height`, `leg_diameter`) hold the rack
plate above the base, open on every side, so drips run down the
jigger's outside and off the rack rather than pooling against a wall
the way they would in a closed caddy.

This rack holds a rinsed bar tool, not food or liquid directly -- the
same clean-tool scope as `grip_stand` holding a tattoo machine rather
than skin -- so it carries none of the food-contact caveats that
`garnish_caddy` needs.
"""

from dataclasses import dataclass

import cadquery as cq


@dataclass(frozen=True)
class JiggerRackParameters:
    """Dimensions for the base, its support legs, and the rack plate."""

    width: float = 220.0
    depth: float = 80.0
    base_thickness: float = 3.0
    corner_radius: float = 6.0

    leg_height: float = 50.0
    leg_diameter: float = 10.0
    leg_inset: float = 14.0

    rack_thickness: float = 4.0
    jigger_count: int = 4
    jigger_hole_diameter: float = 35.0
    jigger_spacing: float = 45.0
    jigger_hole_chamfer: float = 1.5
    rack_edge_margin: float = 8.0

    label: str = "Z$ CAD"
    label_size: float = 5.0
    label_height: float = 0.4

    def leg_positions(self) -> list[tuple[float, float]]:
        """XY center of each of the four corner legs."""
        x = self.width / 2 - self.leg_inset
        y = self.depth / 2 - self.leg_inset
        return [(x, y), (-x, y), (-x, -y), (x, -y)]

    def jigger_hole_centers_x(self) -> list[float]:
        """X center of each jigger hole, left to right."""
        span = (self.jigger_count - 1) * self.jigger_spacing
        start = -span / 2
        return [start + i * self.jigger_spacing for i in range(self.jigger_count)]

    def validate(self) -> None:
        positive_values = {
            "width": self.width,
            "depth": self.depth,
            "base_thickness": self.base_thickness,
            "leg_height": self.leg_height,
            "leg_diameter": self.leg_diameter,
            "rack_thickness": self.rack_thickness,
            "jigger_hole_diameter": self.jigger_hole_diameter,
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

        if self.jigger_count < 1:
            raise ValueError("jigger_count must be at least one")

        leg_radius = self.leg_diameter / 2

        if self.leg_inset < leg_radius:
            raise ValueError(
                "leg_inset is too small for leg_diameter to fit on the base"
            )

        if self.leg_inset > self.width / 2 - leg_radius:
            raise ValueError("leg_inset places legs past the base's centerline")

        if self.leg_inset > self.depth / 2 - leg_radius:
            raise ValueError("leg_inset places legs past the base's centerline")

        if self.jigger_count > 1 and self.jigger_spacing <= self.jigger_hole_diameter:
            raise ValueError("jigger_spacing must exceed jigger_hole_diameter")

        row_span = (
            self.jigger_count - 1
        ) * self.jigger_spacing + self.jigger_hole_diameter

        if row_span > self.width - 2 * self.rack_edge_margin:
            raise ValueError("jigger_count does not fit within the rack width")

        if self.jigger_hole_diameter > self.depth - 2 * self.rack_edge_margin:
            raise ValueError("jigger_hole_diameter does not fit within the rack depth")

        if self.jigger_hole_chamfer < 0:
            raise ValueError("jigger_hole_chamfer cannot be negative")

        if self.jigger_hole_chamfer > 0:
            if self.jigger_hole_chamfer >= self.rack_thickness:
                raise ValueError("jigger_hole_chamfer must be less than rack_thickness")

            countersink_diameter = (
                self.jigger_hole_diameter + 2 * self.jigger_hole_chamfer
            )

            if self.jigger_count > 1 and countersink_diameter >= self.jigger_spacing:
                raise ValueError(
                    "jigger_hole_chamfer makes adjacent countersinks overlap"
                )

            if countersink_diameter > self.depth - 2 * self.rack_edge_margin:
                raise ValueError(
                    "jigger_hole_chamfer does not fit within the rack depth"
                )

        if self.label_size > self.depth - 8:
            raise ValueError("label_size does not fit within the base depth")

        if self.label_size > self.width - 8:
            raise ValueError("label_size does not fit within the base width")


def _hole_cutter(
    *,
    x: float,
    y: float,
    hole_radius: float,
    chamfer: float,
    rack_thickness: float,
    cut_height: float,
) -> cq.Workplane:
    """One jigger hole: a straight bore, plus an optional conical
    countersink at its top mouth so a jigger drops in without
    fumbling for the exact opening."""
    cutter = (
        cq.Workplane("XY")
        .workplane(offset=-1)
        .moveTo(x, y)
        .circle(hole_radius)
        .extrude(cut_height)
    )

    if chamfer > 0:
        frustum = (
            cq.Workplane("XY")
            .workplane(offset=rack_thickness - chamfer)
            .moveTo(x, y)
            .circle(hole_radius)
            .workplane(offset=chamfer)
            .moveTo(x, y)
            .circle(hole_radius + chamfer)
            .loft()
        )
        cutter = cutter.union(frustum)

    return cutter


def build_jigger_rack(parameters: JiggerRackParameters) -> cq.Workplane:
    """Build the base, its support legs, and the perforated rack plate."""
    parameters.validate()

    base = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.base_thickness,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        base = base.edges("|Z").fillet(parameters.corner_radius)

    rack = None

    for x, y in parameters.leg_positions():
        leg = (
            cq.Workplane("XY")
            .workplane(offset=parameters.base_thickness)
            .center(x, y)
            .circle(parameters.leg_diameter / 2)
            .extrude(parameters.leg_height)
        )
        rack = leg if rack is None else rack.union(leg)

    plate = (
        cq.Workplane("XY")
        .workplane(offset=parameters.base_thickness + parameters.leg_height)
        .box(
            parameters.width,
            parameters.depth,
            parameters.rack_thickness,
            centered=(True, True, False),
        )
    )

    if parameters.corner_radius > 0:
        plate = plate.edges("|Z").fillet(parameters.corner_radius)

    rack = rack.union(plate)

    plate_z = parameters.base_thickness + parameters.leg_height
    cut_height = parameters.rack_thickness + 2
    hole_radius = parameters.jigger_hole_diameter / 2

    holes = None

    for x in parameters.jigger_hole_centers_x():
        cutter = _hole_cutter(
            x=x,
            y=0,
            hole_radius=hole_radius,
            chamfer=parameters.jigger_hole_chamfer,
            rack_thickness=parameters.rack_thickness,
            cut_height=cut_height,
        )
        cutter = cutter.translate((0, 0, plate_z))
        holes = cutter if holes is None else holes.union(cutter)

    rack = rack.cut(holes)

    mark = (
        cq.Workplane("XY")
        .workplane(offset=parameters.base_thickness)
        .center(0, -parameters.depth / 2 + parameters.rack_edge_margin)
        .text(
            parameters.label,
            parameters.label_size,
            parameters.label_height,
            halign="center",
            valign="center",
        )
    )

    return base.union(rack).union(mark)
