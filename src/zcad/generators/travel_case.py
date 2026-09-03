"""Travel case for a tattoo-station kit: one object to carry instead
of several loose rectangles.

An open-top crate with a rounded hand-hold cut through each of its two
short end walls, sized loosely to hold this line's other pieces rather
than a custom foam-fitted insert for each one. A generic tote is
simpler to keep working as any of those generators' own dimensions
change, and it's useful on its own for anything else the same size --
it doesn't need to know what's inside it.

The default footprint is sized by the two dimensions that actually
drive it: the stencil holder is the deepest single piece at 210 mm,
and the ink cap tray is the widest at 160 mm. The stencil holder lies
flat on the floor; the interior height leaves roughly 50 mm of
headroom above it for the ink cap tray and grip stand to sit on top,
not laid out beside it -- the three pieces are too mismatched in size
to share one footprint without stacking.

A pair of strap slots near the top rim of each long side wall lets a
bungee cord or strap run across the open top and hold the contents
down -- without a slot span wide enough to risk warping a full
friction-fit lid on FDM. `strap_count` controls how many crossing
points there are.

Straps alone stop things popping out over the top, but they don't
stop the smaller pieces sliding around inside a mostly-empty crate.
Two more features address that directly instead of just enlarging the
crate around the problem:

- `floor_ridge` is a shallow rim on the floor, sized to the stencil
  holder's own footprint, so the largest single piece can't slide
  sideways.
- `tray_ledge` is a pair of internal support ribs partway up the long
  side walls that a separate `insert_tray` (see that generator) rests
  on, holding the ink cap tray and grip stand in their own retention
  wells above the stencil holder instead of loose in the headroom.

The retention geometry makes packing order matter -- stencil holder in
first, insert tray on the ledges second -- which isn't obvious just by
looking at two separate parts. `pack_order_labels` embosses a "1" on
the case floor, inside the ridge, and a "2" on top of one ledge, each
exactly where it stops being visible once that step is done.

Like the rest of this line, it never touches skin or ink -- it's
carried, not worn -- and gets wiped down like any other station
equipment.
"""

from dataclasses import dataclass

import cadquery as cq


@dataclass(frozen=True)
class TravelCaseParameters:
    """Dimensions for the crate shell and its two hand-holds."""

    width: float = 180.0
    depth: float = 245.0
    wall: float = 3.0
    floor_thickness: float = 3.0
    wall_height: float = 100.0
    corner_radius: float = 6.0

    handle_width: float = 90.0
    handle_height: float = 25.0
    handle_top_margin: float = 15.0

    strap_slots: bool = True
    strap_count: int = 2
    strap_spacing: float = 140.0
    strap_slot_width: float = 15.0
    strap_slot_height: float = 8.0
    strap_slot_top_margin: float = 8.0

    floor_ridge: bool = True
    floor_ridge_opening_width: float = 155.0
    floor_ridge_opening_depth: float = 216.0
    floor_ridge_wall: float = 3.0
    floor_ridge_height: float = 4.0

    tray_ledge: bool = True
    tray_ledge_height: float = 55.0
    tray_ledge_thickness: float = 4.0
    tray_ledge_protrusion: float = 6.0
    tray_ledge_end_margin: float = 10.0

    pack_order_labels: bool = True
    pack_order_floor_label_size: float = 12.0
    pack_order_ledge_label_size: float = 4.0
    pack_order_label_height: float = 0.4

    label: str = "Z$ CAD"
    label_size: float = 5.0
    label_height: float = 0.4

    def ledge_center_x(self, side: int) -> float:
        """X center of one tray-ledge rib. `side` is +1 for the right
        wall, -1 for the left wall."""
        interior_width = self.width - 2 * self.wall
        inner_face_x = side * interior_width / 2
        return inner_face_x - side * self.tray_ledge_protrusion / 2

    def strap_positions_y(self) -> list[float]:
        """Y center of each strap crossing point, evenly spaced and
        centered along the case's depth."""
        if self.strap_count < 1:
            return []

        start = -(self.strap_count - 1) * self.strap_spacing / 2
        return [start + index * self.strap_spacing for index in range(self.strap_count)]

    def validate(self) -> None:
        positive_values = {
            "width": self.width,
            "depth": self.depth,
            "wall": self.wall,
            "floor_thickness": self.floor_thickness,
            "wall_height": self.wall_height,
            "handle_width": self.handle_width,
            "handle_height": self.handle_height,
            "label_size": self.label_size,
            "label_height": self.label_height,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.corner_radius < 0:
            raise ValueError("corner_radius cannot be negative")

        if self.handle_top_margin < 0:
            raise ValueError("handle_top_margin cannot be negative")

        if not self.label.strip():
            raise ValueError("label cannot be empty")

        if self.width <= 2 * self.wall:
            raise ValueError("width must exceed twice the wall thickness")

        if self.depth <= 2 * self.wall:
            raise ValueError("depth must exceed twice the wall thickness")

        if self.handle_width < self.handle_height:
            raise ValueError(
                "handle_width must be at least handle_height "
                "for the rounded ends to fit"
            )

        if self.handle_width > self.width - 20:
            raise ValueError("handle_width does not leave enough wall on each side")

        remaining_wall_below_handle = (
            self.wall_height - self.handle_top_margin - self.handle_height
        )

        if remaining_wall_below_handle < 10:
            raise ValueError(
                "handle_top_margin and handle_height leave too little wall "
                "below the hand-hold"
            )

        if self.strap_slots:
            if self.strap_count < 1:
                raise ValueError("strap_count must be at least one")

            if self.strap_slot_width <= 0:
                raise ValueError("strap_slot_width must be greater than zero")

            if self.strap_slot_height <= 0:
                raise ValueError("strap_slot_height must be greater than zero")

            if self.strap_slot_top_margin < 0:
                raise ValueError("strap_slot_top_margin cannot be negative")

            if self.strap_count > 1 and self.strap_spacing <= self.strap_slot_width:
                raise ValueError("strap_spacing must exceed strap_slot_width")

            remaining_wall_below_strap = (
                self.wall_height - self.strap_slot_top_margin - self.strap_slot_height
            )

            if remaining_wall_below_strap < 10:
                raise ValueError(
                    "strap_slot_top_margin and strap_slot_height leave too "
                    "little wall below the slot"
                )

            end_margin = self.corner_radius + 5

            for y_position in self.strap_positions_y():
                if abs(y_position) + self.strap_slot_width / 2 > (
                    self.depth / 2 - end_margin
                ):
                    raise ValueError(
                        "strap slots do not fit within the side wall -- "
                        "reduce strap_count, strap_spacing, or strap_slot_width"
                    )

        interior_width = self.width - 2 * self.wall
        interior_depth = self.depth - 2 * self.wall

        if self.floor_ridge:
            if self.floor_ridge_opening_width <= 0:
                raise ValueError("floor_ridge_opening_width must be greater than zero")

            if self.floor_ridge_opening_depth <= 0:
                raise ValueError("floor_ridge_opening_depth must be greater than zero")

            if self.floor_ridge_wall <= 0:
                raise ValueError("floor_ridge_wall must be greater than zero")

            if self.floor_ridge_height <= 0:
                raise ValueError("floor_ridge_height must be greater than zero")

            if self.floor_ridge_height >= self.wall_height:
                raise ValueError("floor_ridge_height must be less than wall_height")

            ridge_outer_width = (
                self.floor_ridge_opening_width + 2 * self.floor_ridge_wall
            )
            ridge_outer_depth = (
                self.floor_ridge_opening_depth + 2 * self.floor_ridge_wall
            )

            if ridge_outer_width >= interior_width:
                raise ValueError("floor_ridge does not fit within the interior width")

            if ridge_outer_depth >= interior_depth:
                raise ValueError("floor_ridge does not fit within the interior depth")

        if self.tray_ledge:
            if self.tray_ledge_thickness <= 0:
                raise ValueError("tray_ledge_thickness must be greater than zero")

            if self.tray_ledge_protrusion <= 0:
                raise ValueError("tray_ledge_protrusion must be greater than zero")

            if self.tray_ledge_end_margin < 0:
                raise ValueError("tray_ledge_end_margin cannot be negative")

            if self.tray_ledge_protrusion >= interior_width / 2:
                raise ValueError(
                    "tray_ledge_protrusion reaches past the case's centerline"
                )

            if self.floor_ridge and self.tray_ledge_height <= (
                self.floor_ridge_height + self.floor_thickness
            ):
                raise ValueError(
                    "tray_ledge_height must clear the floor_ridge's own height"
                )

            if self.tray_ledge_height >= self.floor_thickness + self.wall_height:
                raise ValueError("tray_ledge_height does not fit under the rim")

            ledge_span = interior_depth - 2 * self.tray_ledge_end_margin

            if ledge_span <= 0:
                raise ValueError(
                    "tray_ledge_end_margin leaves no room for the support ribs"
                )

        if self.pack_order_labels:
            if self.pack_order_floor_label_size <= 0:
                raise ValueError(
                    "pack_order_floor_label_size must be greater than zero"
                )

            if self.pack_order_ledge_label_size <= 0:
                raise ValueError(
                    "pack_order_ledge_label_size must be greater than zero"
                )

            if self.pack_order_label_height <= 0:
                raise ValueError("pack_order_label_height must be greater than zero")

            if self.floor_ridge and self.pack_order_floor_label_size > (
                min(self.floor_ridge_opening_width, self.floor_ridge_opening_depth) - 4
            ):
                raise ValueError(
                    "pack_order_floor_label_size does not fit within the "
                    "floor_ridge opening"
                )

            if self.tray_ledge and self.pack_order_ledge_label_size > (
                self.tray_ledge_protrusion - 1
            ):
                raise ValueError(
                    "pack_order_ledge_label_size does not fit on the tray_ledge"
                )


def _handle_cutter(
    parameters: TravelCaseParameters,
    y_position: float,
) -> cq.Workplane:
    """One rounded hand-hold slot, cut through an end wall."""
    center_z = (
        parameters.floor_thickness
        + parameters.wall_height
        - parameters.handle_top_margin
        - parameters.handle_height / 2
    )

    cutter = (
        cq.Workplane("XY")
        .workplane(offset=center_z - parameters.handle_height / 2)
        .center(0, y_position)
        .box(
            parameters.handle_width,
            parameters.wall + 2,
            parameters.handle_height,
            centered=(True, True, False),
        )
    )

    # A radius of exactly half the height would give a true stadium
    # shape, but that tangent case trips up the fillet kernel; staying
    # just under it keeps the rounded look without the failure.
    return cutter.edges("|Y").fillet(parameters.handle_height * 0.45)


def _strap_slot_cutter(
    parameters: TravelCaseParameters,
    x_position: float,
    y_position: float,
) -> cq.Workplane:
    """One strap slot, cut through a long side wall near the rim."""
    slot_top_z = (
        parameters.floor_thickness
        + parameters.wall_height
        - parameters.strap_slot_top_margin
    )
    slot_bottom_z = slot_top_z - parameters.strap_slot_height

    return (
        cq.Workplane("XY")
        .workplane(offset=slot_bottom_z)
        .center(x_position, y_position)
        .box(
            parameters.wall + 2,
            parameters.strap_slot_width,
            parameters.strap_slot_height,
            centered=(True, True, False),
        )
    )


def _floor_ridge(
    parameters: TravelCaseParameters,
) -> cq.Workplane:
    """A shallow rim on the floor sized to the stencil holder's own
    footprint, so it can't slide sideways."""
    outer_width = parameters.floor_ridge_opening_width + 2 * parameters.floor_ridge_wall
    outer_depth = parameters.floor_ridge_opening_depth + 2 * parameters.floor_ridge_wall

    outer = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor_thickness)
        .box(
            outer_width,
            outer_depth,
            parameters.floor_ridge_height,
            centered=(True, True, False),
        )
    )

    inner = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor_thickness - 0.5)
        .box(
            parameters.floor_ridge_opening_width,
            parameters.floor_ridge_opening_depth,
            parameters.floor_ridge_height + 1,
            centered=(True, True, False),
        )
    )

    return outer.cut(inner)


def _tray_ledge(
    parameters: TravelCaseParameters,
    side: int,
) -> cq.Workplane:
    """One support rib on the inside of a long side wall, for the
    insert tray to rest on. `side` is +1 for the right wall, -1 for
    the left wall."""
    ledge_span = (
        parameters.depth - 2 * parameters.wall - 2 * parameters.tray_ledge_end_margin
    )
    center_x = parameters.ledge_center_x(side)

    return (
        cq.Workplane("XY")
        .workplane(
            offset=parameters.tray_ledge_height - parameters.tray_ledge_thickness
        )
        .center(center_x, 0)
        .box(
            parameters.tray_ledge_protrusion,
            ledge_span,
            parameters.tray_ledge_thickness,
            centered=(True, True, False),
        )
    )


def build_travel_case(
    parameters: TravelCaseParameters,
) -> cq.Workplane:
    """Build the crate shell and its two hand-holds."""
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

    case = outer.cut(inner)

    for y_position in (-parameters.depth / 2, parameters.depth / 2):
        case = case.cut(_handle_cutter(parameters, y_position))

    if parameters.strap_slots:
        for x_position in (-parameters.width / 2, parameters.width / 2):
            for y_position in parameters.strap_positions_y():
                case = case.cut(_strap_slot_cutter(parameters, x_position, y_position))

    if parameters.floor_ridge:
        case = case.union(_floor_ridge(parameters))

    if parameters.tray_ledge:
        for side in (-1, 1):
            case = case.union(_tray_ledge(parameters, side))

    if parameters.pack_order_labels:
        floor_step = (
            cq.Workplane("XY")
            .workplane(offset=parameters.floor_thickness)
            .center(0, 0)
            .text(
                "1",
                parameters.pack_order_floor_label_size,
                parameters.pack_order_label_height,
                halign="center",
                valign="center",
            )
        )
        case = case.union(floor_step)

        if parameters.tray_ledge:
            ledge_step = (
                cq.Workplane("XY")
                .workplane(offset=parameters.tray_ledge_height)
                .center(parameters.ledge_center_x(1), 0)
                .text(
                    "2",
                    parameters.pack_order_ledge_label_size,
                    parameters.pack_order_label_height,
                    halign="center",
                    valign="center",
                )
            )
            case = case.union(ledge_step)

    y_back_face = parameters.depth / 2

    mark = (
        cq.Workplane("XZ")
        .workplane(offset=-(y_back_face + parameters.label_height))
        .center(0, parameters.floor_thickness + parameters.wall_height * 0.25)
        .text(
            parameters.label,
            parameters.label_size,
            parameters.label_height,
            halign="center",
            valign="center",
        )
    )

    return case.union(mark)
