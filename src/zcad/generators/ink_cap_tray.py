"""Ink cap tray for a tattoo station: a row of disposable ink caps held
upright over a spill-catching basin.

Caps sit in a row of snug through-holes in a rack, so a knocked-over or
overfilled cap drains down into the basin instead of pooling on the
station surface. The basin comes in two styles:

- `"standalone"` (the default): a plain, fully enclosed tray -- walls
  on all four sides, flat floor. Most tattoo stations are a rolling
  cart or an arm-mounted tray, not sink-adjacent, so this is the style
  that works anywhere.
- `"sink_edge"`: reuses the same sloped, spout-fed basin as `drip_tray`
  and `sponge_caddy`, for the less common station that does sit at a
  sink and can drain into it directly.

The standalone basin also cuts a shallow retention groove around the
inside of its wall near the top rim (`liner_groove`). Tucking a
disposable plastic liner's edge into that groove keeps it taut instead
of sliding down into the basin mid-session, so cleanup between clients
is peel-out-and-discard rather than scrubbing the tray itself.

Three more workflow refinements, all on by default:

- `cap_hole_chamfer` countersinks each cap hole's mouth, so a gloved
  hand can drop a cap in or pluck it back out without fumbling for the
  exact opening.
- `cap_labels` embosses a number next to each hole, so a color can be
  assigned to a position consistently across sessions.
- `foot_pockets` recesses four shallow pockets into the standalone
  basin's underside for adhesive rubber feet, so the tray doesn't
  slide during one-handed operation.

An optional pair of larger `mixing_well_count` wells extends the row
past its last small cap, for the bigger caps some sessions use to mix
colors or hold more volume. Off by default (`mixing_well_count=0`)
since they cost rack footprint whether or not a session needs them.

Like every other clean-zone accessory here, this tray never contacts
skin, blood, or ink directly -- caps are single-use and disposed of
after the session; the tray itself gets wiped down and covered in
barrier film like the rest of the station.
"""

from dataclasses import dataclass, fields

import cadquery as cq

from zcad.generators.drainage_basin import (
    DrainageBasinParameters,
    build_drainage_basin,
)

ModelParts = dict[str, cq.Workplane]

_BASIN_FIELD_NAMES = {field.name for field in fields(DrainageBasinParameters)}
_BASIN_STYLES = {"standalone", "sink_edge"}


@dataclass(frozen=True)
class InkCapTrayParameters:
    """Dimensions for the basin body and its ink-cap rack."""

    width: float
    depth: float
    wall: float = 3.0
    basin_height: float = 16.0
    floor_back: float = 6.0
    floor_front: float = 2.6
    spout_length: float = 30.0
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

    rack_thickness: float = 4.0
    rack_edge_margin: float = 10.0

    cap_diameter: float = 13.0
    cap_hole_clearance: float = 0.4
    cap_count: int = 6
    cap_spacing: float = 20.0

    basin_style: str = "standalone"
    standalone_floor: float = 3.0

    liner_groove: bool = True
    liner_groove_depth: float = 0.8
    liner_groove_width: float = 1.6
    liner_groove_offset: float = 4.0

    cap_hole_chamfer: float = 1.0

    cap_labels: bool = True
    cap_label_size: float = 3.0
    cap_label_height: float = 0.3
    cap_label_offset: float = 3.0

    foot_pockets: bool = True
    foot_diameter: float = 10.0
    foot_depth: float = 1.5
    foot_inset: float = 14.0

    mixing_well_count: int = 0
    mixing_well_diameter: float = 30.0
    mixing_well_spacing: float = 36.0
    mixing_well_margin: float = 12.0

    def basin_parameters(self) -> DrainageBasinParameters:
        """The subset of fields the shared drainage basin needs."""
        values = {
            name: getattr(self, name)
            for name in _BASIN_FIELD_NAMES
            if hasattr(self, name)
        }
        return DrainageBasinParameters(**values)

    @property
    def cap_hole_diameter(self) -> float:
        return self.cap_diameter + self.cap_hole_clearance

    def cap_positions(self) -> list[tuple[float, float]]:
        """Center points of each ink-cap hole, evenly spaced in a
        single row along X, centered on the rack."""
        start = -(self.cap_count - 1) * self.cap_spacing / 2
        return [
            (start + index * self.cap_spacing, 0.0) for index in range(self.cap_count)
        ]

    def mixing_well_positions(self) -> list[tuple[float, float]]:
        """Center points of the larger mixing wells, continuing the
        row past its last (rightmost) small cap."""
        if self.mixing_well_count < 1:
            return []

        row_edge_x = (
            max(x for x, _y in self.cap_positions()) + self.cap_hole_diameter / 2
        )
        group_start_x = (
            row_edge_x + self.mixing_well_margin + self.mixing_well_diameter / 2
        )

        return [
            (group_start_x + index * self.mixing_well_spacing, 0.0)
            for index in range(self.mixing_well_count)
        ]

    def hole_positions(self) -> list[tuple[float, float, float]]:
        """Every rack hole as `(x, y, radius)`: the small cap row
        followed by the larger mixing wells, in the order each gets
        numbered."""
        small_radius = self.cap_hole_diameter / 2
        mixing_radius = self.mixing_well_diameter / 2

        return [(x, y, small_radius) for x, y in self.cap_positions()] + [
            (x, y, mixing_radius) for x, y in self.mixing_well_positions()
        ]

    def validate(self) -> None:
        if self.basin_style not in _BASIN_STYLES:
            raise ValueError(f"basin_style must be one of {sorted(_BASIN_STYLES)}")

        if self.basin_style == "sink_edge":
            self.basin_parameters().validate()
        else:
            if self.wall <= 0:
                raise ValueError("wall must be greater than zero")

            if self.basin_height <= 0:
                raise ValueError("basin_height must be greater than zero")

            if self.corner_radius < 0:
                raise ValueError("corner_radius cannot be negative")

            if self.standalone_floor <= 0:
                raise ValueError("standalone_floor must be greater than zero")

            if self.standalone_floor >= self.basin_height:
                raise ValueError("standalone_floor must be less than basin_height")

            if self.label_size <= 0:
                raise ValueError("label_size must be greater than zero")

            if self.label_height <= 0:
                raise ValueError("label_height must be greater than zero")

            if not self.label.strip():
                raise ValueError("label cannot be empty")

            if self.liner_groove:
                if self.liner_groove_depth <= 0:
                    raise ValueError("liner_groove_depth must be greater than zero")

                if self.liner_groove_width <= 0:
                    raise ValueError("liner_groove_width must be greater than zero")

                if self.liner_groove_offset <= 0:
                    raise ValueError("liner_groove_offset must be greater than zero")

                if self.liner_groove_depth >= self.wall:
                    raise ValueError("liner_groove_depth must be less than wall")

                groove_top = (
                    self.basin_height
                    - self.liner_groove_offset
                    + self.liner_groove_width / 2
                )
                groove_bottom = (
                    self.basin_height
                    - self.liner_groove_offset
                    - self.liner_groove_width / 2
                )

                if groove_top > self.basin_height:
                    raise ValueError(
                        "liner_groove_offset places the groove above the rim"
                    )

                if groove_bottom < self.standalone_floor:
                    raise ValueError(
                        "liner_groove_offset places the groove below the floor"
                    )

            if self.width <= 2 * self.wall:
                raise ValueError("width must exceed twice the wall thickness")

            if self.depth <= 2 * self.wall:
                raise ValueError("depth must exceed twice the wall thickness")

        positive_values = {
            "rack_thickness": self.rack_thickness,
            "cap_diameter": self.cap_diameter,
            "cap_spacing": self.cap_spacing,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.cap_hole_clearance < 0:
            raise ValueError("cap_hole_clearance cannot be negative")

        if self.rack_edge_margin < 0:
            raise ValueError("rack_edge_margin cannot be negative")

        if self.cap_count < 1:
            raise ValueError("cap_count must be at least one")

        if self.cap_hole_diameter >= self.cap_spacing:
            raise ValueError("cap_hole_diameter must be smaller than cap_spacing")

        row_span = (self.cap_count - 1) * self.cap_spacing + self.cap_hole_diameter
        interior_width = self.width - 2 * self.wall

        if row_span >= interior_width - 2 * self.rack_edge_margin:
            raise ValueError("ink cap row does not fit within the rack width")

        if self.cap_hole_diameter >= self.depth - 2 * self.rack_edge_margin:
            raise ValueError("cap_hole_diameter does not fit within the rack depth")

        if self.cap_hole_chamfer < 0:
            raise ValueError("cap_hole_chamfer cannot be negative")

        if self.cap_hole_chamfer > 0:
            if self.cap_hole_chamfer >= self.rack_thickness:
                raise ValueError("cap_hole_chamfer must be less than rack_thickness")

            countersink_diameter = self.cap_hole_diameter + 2 * self.cap_hole_chamfer

            if countersink_diameter >= self.cap_spacing:
                raise ValueError("cap_hole_chamfer makes adjacent countersinks overlap")

            if countersink_diameter >= self.depth - 2 * self.rack_edge_margin:
                raise ValueError("cap_hole_chamfer does not fit within the rack depth")

        if self.cap_labels:
            if self.cap_label_size <= 0:
                raise ValueError("cap_label_size must be greater than zero")

            if self.cap_label_height <= 0:
                raise ValueError("cap_label_height must be greater than zero")

            if self.cap_label_offset < 0:
                raise ValueError("cap_label_offset cannot be negative")

            label_reach = (
                self.cap_hole_diameter / 2 + self.cap_label_offset + self.cap_label_size
            )

            if label_reach >= self.depth / 2:
                raise ValueError("cap_label does not fit within the rack depth")

        if self.basin_style == "standalone" and self.foot_pockets:
            if self.foot_diameter <= 0:
                raise ValueError("foot_diameter must be greater than zero")

            if self.foot_depth <= 0:
                raise ValueError("foot_depth must be greater than zero")

            if self.foot_inset <= 0:
                raise ValueError("foot_inset must be greater than zero")

            if self.foot_depth >= self.standalone_floor:
                raise ValueError("foot_depth must be less than standalone_floor")

            if self.foot_inset < self.foot_diameter / 2:
                raise ValueError("foot_inset is too small for foot_diameter")

            if self.foot_inset >= self.width / 2 or self.foot_inset >= self.depth / 2:
                raise ValueError("foot_inset places the feet outside the basin")

            if self.width - 2 * self.foot_inset <= self.foot_diameter:
                raise ValueError("foot pockets overlap across the width")

            if self.depth - 2 * self.foot_inset <= self.foot_diameter:
                raise ValueError("foot pockets overlap across the depth")

        if self.mixing_well_count < 0:
            raise ValueError("mixing_well_count cannot be negative")

        if self.mixing_well_count > 0:
            if self.mixing_well_diameter <= 0:
                raise ValueError("mixing_well_diameter must be greater than zero")

            if self.mixing_well_margin < 0:
                raise ValueError("mixing_well_margin cannot be negative")

            if self.mixing_well_count > 1 and (
                self.mixing_well_spacing <= self.mixing_well_diameter
            ):
                raise ValueError("mixing_well_spacing must exceed mixing_well_diameter")

            mixing_chamfer_allowance = (
                2 * self.cap_hole_chamfer if self.cap_hole_chamfer > 0 else 0
            )

            if self.mixing_well_diameter + mixing_chamfer_allowance >= (
                self.depth - 2 * self.rack_edge_margin
            ):
                raise ValueError(
                    "mixing_well_diameter does not fit within the rack depth"
                )

            last_well_x = self.mixing_well_positions()[-1][0]
            group_end_x = last_well_x + self.mixing_well_diameter / 2
            interior_width = self.width - 2 * self.wall

            if group_end_x >= interior_width / 2 - self.rack_edge_margin:
                raise ValueError(
                    "mixing wells do not fit within the rack width -- "
                    "increase width or reduce mixing_well_count"
                )

            if self.cap_labels:
                mixing_label_reach = (
                    self.mixing_well_diameter / 2
                    + self.cap_label_offset
                    + self.cap_label_size
                )

                if mixing_label_reach >= self.depth / 2:
                    raise ValueError("cap_label does not fit next to the mixing wells")


def _hole_cutter(
    *,
    x: float,
    y: float,
    hole_radius: float,
    chamfer: float,
    rack_thickness: float,
    cut_height: float,
) -> cq.Workplane:
    """One cap hole: a straight bore, plus an optional conical
    countersink at its top mouth so a gloved hand can find and clear
    the opening without fumbling."""
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


def _build_rack(
    parameters: InkCapTrayParameters,
) -> cq.Workplane:
    """Build the rack: a plate with a row of through-holes, each sized
    to snugly hold one disposable ink cap upright."""
    plate = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.rack_thickness,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        plate = plate.edges("|Z").fillet(parameters.corner_radius)

    cut_height = parameters.rack_thickness + 2
    positions = parameters.hole_positions()

    holes = None

    for x, y, radius in positions:
        cutter = _hole_cutter(
            x=x,
            y=y,
            hole_radius=radius,
            chamfer=parameters.cap_hole_chamfer,
            rack_thickness=parameters.rack_thickness,
            cut_height=cut_height,
        )
        holes = cutter if holes is None else holes.union(cutter)

    plate = plate.cut(holes)

    if parameters.cap_labels:
        for index, (x, y, radius) in enumerate(positions, start=1):
            label_y = y + radius + parameters.cap_label_offset

            mark = (
                cq.Workplane("XY")
                .workplane(offset=parameters.rack_thickness)
                .center(x, label_y)
                .text(
                    str(index),
                    parameters.cap_label_size,
                    parameters.cap_label_height,
                    halign="center",
                    valign="center",
                )
            )
            plate = plate.union(mark)

    return plate


def _build_standalone_basin(
    parameters: InkCapTrayParameters,
) -> cq.Workplane:
    """Build a fully enclosed catch basin: walls on all four sides, a
    flat floor. Assumes no sink to drain into -- anything spilled just
    sits in the basin until it's wiped out."""
    outer = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.basin_height,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        outer = outer.edges("|Z").fillet(parameters.corner_radius)

    inner = (
        cq.Workplane("XY")
        .workplane(offset=parameters.standalone_floor)
        .box(
            parameters.width - 2 * parameters.wall,
            parameters.depth - 2 * parameters.wall,
            parameters.basin_height - parameters.standalone_floor,
            centered=(True, True, False),
        )
    )

    body = outer.cut(inner)

    if parameters.liner_groove:
        groove_z = parameters.basin_height - parameters.liner_groove_offset
        groove_wall_remaining = parameters.wall - parameters.liner_groove_depth

        groove_cutter = (
            cq.Workplane("XY")
            .workplane(offset=groove_z - parameters.liner_groove_width / 2)
            .box(
                parameters.width - 2 * groove_wall_remaining,
                parameters.depth - 2 * groove_wall_remaining,
                parameters.liner_groove_width,
                centered=(True, True, False),
            )
        )
        body = body.cut(groove_cutter)

    if parameters.foot_pockets:
        foot_x = parameters.width / 2 - parameters.foot_inset
        foot_y = parameters.depth / 2 - parameters.foot_inset
        foot_positions = [
            (sx * foot_x, sy * foot_y) for sx in (-1, 1) for sy in (-1, 1)
        ]

        pockets = None

        for x, y in foot_positions:
            pocket = (
                cq.Workplane("XY")
                .workplane(offset=-0.5)
                .center(x, y)
                .circle(parameters.foot_diameter / 2)
                .extrude(parameters.foot_depth + 0.5)
            )
            pockets = pocket if pockets is None else pockets.union(pocket)

        body = body.cut(pockets)

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

    return body.union(mark)


def build_ink_cap_tray(
    parameters: InkCapTrayParameters,
) -> ModelParts:
    """Build the basin and its ink-cap rack."""
    parameters.validate()

    if parameters.basin_style == "sink_edge":
        basin = build_drainage_basin(parameters.basin_parameters())
    else:
        basin = _build_standalone_basin(parameters)

    return {
        "basin": basin,
        "rack": _build_rack(parameters),
    }
