"""Insert tray for the tattoo-line travel case.

A flat plate that rests on the `travel_case` generator's internal
`tray_ledge` ribs, above the stencil holder sitting on the case floor.
Two shallow-walled retention wells -- one sized for the grip stand's
footprint, one for the ink cap tray's -- keep those two pieces from
sliding around in transit instead of floating loose in the case's
headroom. The tray lifts straight out to reach the stencil holder
below it.

The well walls are shallow (6-8 mm) on purpose: they only need to stop
lateral sliding, not fully enclose either piece, since both stand
taller than that once resting in their well.

Like the rest of this line, it never touches skin or ink and gets
wiped down like any other station accessory.
"""

from dataclasses import dataclass

import cadquery as cq

ModelParts = dict[str, cq.Workplane]


@dataclass(frozen=True)
class InsertTrayParameters:
    """Dimensions for the tray plate and its two retention wells."""

    width: float = 170.0
    depth: float = 215.0
    floor_thickness: float = 3.0
    corner_radius: float = 4.0

    grip_stand_well_width: float = 66.0
    grip_stand_well_depth: float = 102.0
    grip_stand_well_wall: float = 3.0
    grip_stand_well_wall_height: float = 8.0

    ink_cap_tray_well_width: float = 162.0
    ink_cap_tray_well_depth: float = 96.0
    ink_cap_tray_well_wall: float = 3.0
    ink_cap_tray_well_wall_height: float = 6.0

    well_gap: float = 8.0

    label: str = "Z$ CAD"
    label_size: float = 4.0
    label_height: float = 0.3

    def well_centers_y(self) -> tuple[float, float]:
        """Y center of the grip-stand well, then the ink-cap-tray
        well, front to back."""
        span = self.grip_stand_well_depth + self.well_gap + self.ink_cap_tray_well_depth
        start = -span / 2

        grip_stand_y = start + self.grip_stand_well_depth / 2
        ink_cap_tray_y = (
            start
            + self.grip_stand_well_depth
            + self.well_gap
            + self.ink_cap_tray_well_depth / 2
        )

        return (grip_stand_y, ink_cap_tray_y)

    def validate(self) -> None:
        positive_values = {
            "width": self.width,
            "depth": self.depth,
            "floor_thickness": self.floor_thickness,
            "grip_stand_well_width": self.grip_stand_well_width,
            "grip_stand_well_depth": self.grip_stand_well_depth,
            "grip_stand_well_wall": self.grip_stand_well_wall,
            "grip_stand_well_wall_height": self.grip_stand_well_wall_height,
            "ink_cap_tray_well_width": self.ink_cap_tray_well_width,
            "ink_cap_tray_well_depth": self.ink_cap_tray_well_depth,
            "ink_cap_tray_well_wall": self.ink_cap_tray_well_wall,
            "ink_cap_tray_well_wall_height": self.ink_cap_tray_well_wall_height,
            "well_gap": self.well_gap,
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

        for name, well_width, well_wall in (
            ("grip_stand_well", self.grip_stand_well_width, self.grip_stand_well_wall),
            (
                "ink_cap_tray_well",
                self.ink_cap_tray_well_width,
                self.ink_cap_tray_well_wall,
            ),
        ):
            outer_width = well_width + 2 * well_wall

            if outer_width >= self.width:
                raise ValueError(
                    f"{name} (with its wall) does not fit within the tray width"
                )

        total_wells_depth = (
            self.grip_stand_well_depth + self.well_gap + self.ink_cap_tray_well_depth
        )

        if total_wells_depth >= self.depth:
            raise ValueError("the two wells do not fit within the tray depth")


def _well(
    center_y: float,
    opening_width: float,
    opening_depth: float,
    wall: float,
    wall_height: float,
    floor_thickness: float,
) -> cq.Workplane:
    """One shallow-walled retention well: a rectangular rim standing
    on the tray floor, open in the middle for an item to drop into."""
    outer = (
        cq.Workplane("XY")
        .workplane(offset=floor_thickness)
        .center(0, center_y)
        .box(
            opening_width + 2 * wall,
            opening_depth + 2 * wall,
            wall_height,
            centered=(True, True, False),
        )
    )

    inner = (
        cq.Workplane("XY")
        .workplane(offset=floor_thickness - 0.5)
        .center(0, center_y)
        .box(
            opening_width,
            opening_depth,
            wall_height + 1,
            centered=(True, True, False),
        )
    )

    return outer.cut(inner)


def build_insert_tray(
    parameters: InsertTrayParameters,
) -> cq.Workplane:
    """Build the tray plate and its two retention wells."""
    parameters.validate()

    plate = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.floor_thickness,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        plate = plate.edges("|Z").fillet(parameters.corner_radius)

    grip_stand_y, ink_cap_tray_y = parameters.well_centers_y()

    grip_stand_well = _well(
        grip_stand_y,
        parameters.grip_stand_well_width,
        parameters.grip_stand_well_depth,
        parameters.grip_stand_well_wall,
        parameters.grip_stand_well_wall_height,
        parameters.floor_thickness,
    )

    ink_cap_tray_well = _well(
        ink_cap_tray_y,
        parameters.ink_cap_tray_well_width,
        parameters.ink_cap_tray_well_depth,
        parameters.ink_cap_tray_well_wall,
        parameters.ink_cap_tray_well_wall_height,
        parameters.floor_thickness,
    )

    tray = plate.union(grip_stand_well).union(ink_cap_tray_well)

    y_back_face = parameters.depth / 2

    mark = (
        cq.Workplane("XZ")
        .workplane(offset=-(y_back_face + parameters.label_height))
        .center(0, parameters.floor_thickness / 2)
        .text(
            parameters.label,
            parameters.label_size,
            parameters.label_height,
            halign="center",
            valign="center",
        )
    )

    return tray.union(mark)
