"""Shared sink-edge drainage basin: sloped floor + flaring/curving spout.

Any product that needs to keep a wet item elevated above a floor that
self-drains into the sink -- rather than pooling under it -- builds its
basin from this. The basin floor tapers continuously from a back wall
down to an open, wall-less spout that cantilevers past the counter edge
and flares wider at its tip, so collected water releases directly into
the sink instead of pooling under whatever sits on top. The tip's
leading edge is straight by default (matched to a straight counter/sink
edge) but can optionally take on a concave, swallow-tail arc that
reaches further at its corners than at its centerline, to track the way
a round or oval sink's cutout curves away from the basin at the sides.

`drip_tray` and `sponge_caddy` both build their basin from here and
differ only in what sits on top of it.
"""

import math
from dataclasses import dataclass

import cadquery as cq

ZRange = tuple[float, float]


@dataclass(frozen=True)
class DrainageBasinParameters:
    """Dimensions for the sloped, self-draining basin body."""

    width: float
    depth: float
    wall: float = 3.0
    basin_height: float = 14.0
    floor_back: float = 5.0
    floor_front: float = 2.4
    spout_length: float = 28.0
    spout_tip_thickness: float = 1.4
    spout_flare_margin: float = 15.0
    spout_tip_bulge: float = 0.0
    spout_tip_fillet: float = 6.0
    corner_radius: float = 5.0

    drip_groove: bool = True
    groove_depth: float = 0.5
    groove_width: float = 2.0
    groove_offset_from_tip: float = 5.0

    label: str = "Z$ CAD"
    label_size: float = 4.0
    label_height: float = 0.4

    def validate(self) -> None:
        positive_values = {
            "width": self.width,
            "depth": self.depth,
            "wall": self.wall,
            "basin_height": self.basin_height,
            "floor_back": self.floor_back,
            "floor_front": self.floor_front,
            "spout_length": self.spout_length,
            "spout_tip_thickness": self.spout_tip_thickness,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.corner_radius < 0:
            raise ValueError("corner_radius cannot be negative")

        if self.spout_flare_margin < 0:
            raise ValueError("spout_flare_margin cannot be negative")

        if self.spout_tip_bulge < 0:
            raise ValueError("spout_tip_bulge cannot be negative")

        if self.spout_tip_fillet < 0:
            raise ValueError("spout_tip_fillet cannot be negative")

        if self.label_size <= 0:
            raise ValueError("label_size must be greater than zero")

        if self.label_height <= 0:
            raise ValueError("label_height must be greater than zero")

        if not self.label.strip():
            raise ValueError("label cannot be empty")

        if self.width <= 2 * self.wall:
            raise ValueError("width must exceed twice the wall thickness")

        if self.depth <= self.wall:
            raise ValueError("depth must exceed the back wall thickness")

        if self.basin_height <= self.floor_back:
            raise ValueError("basin_height must exceed floor_back")

        if self.floor_front >= self.floor_back:
            raise ValueError(
                "floor_front must be less than floor_back so the basin "
                "floor slopes down toward the spout"
            )

        if self.spout_tip_thickness >= self.floor_front:
            raise ValueError(
                "spout_tip_thickness must be less than floor_front so the "
                "spout keeps tapering down to a thin drip edge"
            )

        if self.drip_groove:
            if self.groove_offset_from_tip >= self.spout_length:
                raise ValueError(
                    "groove_offset_from_tip must be less than spout_length"
                )

            if self.groove_depth >= self.spout_tip_thickness:
                raise ValueError("groove_depth must be less than spout_tip_thickness")


def _edge_centered_near(
    edge: cq.Edge,
    x: float,
    y: float,
    tolerance: float = 0.5,
) -> bool:
    """True if a vertical edge's midpoint sits near the given (x, y)."""
    center = edge.Center()
    return abs(center.x - x) < tolerance and abs(center.y - y) < tolerance


def _tapered_block(
    *,
    y0: float,
    y1: float,
    x0: float,
    x1: float,
    z0: ZRange,
    z1: ZRange,
) -> cq.Workplane:
    """Loft a block from y0 to y1 whose cross-section (width, z-range)
    at each end is given by (x0, z0) and (x1, z1). Used both to cut a
    sloped basin floor (z varies, x constant) and to model the spout
    tongue directly as a solid that flares in width and tapers in
    thickness at the same time (x and z both vary)."""
    profile = (
        cq.Workplane("XZ")
        .workplane(offset=-y0)
        .moveTo(0, (z0[0] + z0[1]) / 2)
        .rect(x0, z0[1] - z0[0])
    )

    profile = (
        profile.workplane(offset=-(y1 - y0))
        .moveTo(0, (z1[0] + z1[1]) / 2)
        .rect(x1, z1[1] - z1[0])
    )

    return profile.loft()


def interior_width(parameters: DrainageBasinParameters) -> float:
    """Usable width inside the basin's side walls."""
    return parameters.width - 2 * parameters.wall


def tip_width(parameters: DrainageBasinParameters) -> float:
    """Width of the spout at its flared tip (before any curved cap)."""
    return interior_width(parameters) + 2 * parameters.spout_flare_margin


def build_drainage_basin(
    parameters: DrainageBasinParameters,
) -> cq.Workplane:
    """Build the basin with a continuously sloped, flaring, wall-less
    spout."""
    parameters.validate()

    basin_interior_width = interior_width(parameters)
    basin_tip_width = tip_width(parameters)

    y_back = -parameters.depth / 2 + parameters.wall
    y_front = parameters.depth / 2
    y_tip = parameters.depth / 2 + parameters.spout_length

    outer = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.basin_height,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        outer = outer.edges("|Z and <Y").fillet(parameters.corner_radius)

    cutter_top = parameters.basin_height + 20

    basin_cutter = _tapered_block(
        y0=y_back,
        y1=y_front,
        x0=basin_interior_width,
        x1=basin_interior_width,
        z0=(parameters.floor_back, cutter_top),
        z1=(parameters.floor_front, cutter_top),
    )

    spout_solid = _tapered_block(
        y0=y_front,
        y1=y_tip,
        x0=basin_interior_width,
        x1=basin_tip_width,
        z0=(0.0, parameters.floor_front),
        z1=(0.0, parameters.spout_tip_thickness),
    )

    body = outer.cut(basin_cutter).union(spout_solid)

    if parameters.spout_tip_bulge > 0:
        # A round or oval sink's cutout is closest to the tray on the
        # centerline and curves away toward the sides, so the tip should
        # reach *further* at its corners than at its center to clear that
        # curve with even margin. Each half is built as its own simple
        # wire (arc + two straight edges) because a single wire spanning
        # both corners would touch itself at the center pinch point.
        #
        # The arc's middle control point is placed exactly on the circle
        # through the center point and the corner point whose center of
        # curvature lies on the Y axis, which makes the two mirrored
        # halves meet at the center with a matching (horizontal) tangent
        # instead of a visible kink -- no fillet needed there.
        half_width = basin_tip_width / 2
        bulge = parameters.spout_tip_bulge
        radius = (half_width**2 + bulge**2) / (2 * bulge)
        arc_center_y = y_tip + radius

        seam_fillet = min(parameters.spout_tip_fillet * 0.4, 3.0)

        for side in (-1, 1):
            corner_x = side * half_width
            mid_x = side * half_width / 2
            mid_y = arc_center_y - math.sqrt(radius**2 - mid_x**2)
            corner = (corner_x, y_tip + bulge)

            side_cap = (
                cq.Workplane("XY")
                .moveTo(0, y_tip)
                .threePointArc((mid_x, mid_y), corner)
                .lineTo(corner_x, y_tip)
                .close()
                .extrude(parameters.spout_tip_thickness)
            )

            if parameters.spout_tip_fillet > 0:
                wingtip_edges = [
                    edge
                    for edge in side_cap.edges("|Z").vals()
                    if _edge_centered_near(edge, *corner)
                ]

                if wingtip_edges:
                    side_cap = side_cap.newObject(wingtip_edges).fillet(
                        parameters.spout_tip_fillet
                    )

            body = body.union(side_cap)

        if seam_fillet > 0:
            seam_edges = [
                edge
                for edge in body.edges("|Z").vals()
                if _edge_centered_near(edge, -half_width, y_tip)
                or _edge_centered_near(edge, half_width, y_tip)
            ]

            if seam_edges:
                body = body.newObject(seam_edges).fillet(seam_fillet)

    if parameters.drip_groove:
        y_groove = y_tip - parameters.groove_offset_from_tip

        groove = (
            cq.Workplane("XY")
            .box(
                basin_tip_width + 4,
                parameters.groove_width,
                parameters.groove_depth + 1.0,
                centered=(True, True, False),
            )
            .translate((0, y_groove - parameters.groove_width / 2, -1.0))
        )

        body = body.cut(groove)

    y_back_face = -parameters.depth / 2

    mark = (
        cq.Workplane("XZ")
        .workplane(offset=-y_back_face)
        .center(0, parameters.basin_height / 2)
        .text(
            parameters.label,
            parameters.label_size,
            parameters.label_height,
            halign="center",
            valign="center",
        )
    )
    body = body.union(mark)

    return body
