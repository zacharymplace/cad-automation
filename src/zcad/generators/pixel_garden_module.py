"""Pixel garden module: one plantable pixel that dovetails to its
neighbours.

Each module is a square cup with a drainage hole. A vertical dovetail
rail runs down its +X and +Y faces and a matching slot is cut into
its -X and -Y faces, so any number of modules slide together from
above into any pixel image: a heart, a mushroom, a name. The rail
tip is `rail_depth` proud of the wall and the slot swallows it
with clearance, so the assembled pitch is one `size` per pixel. The
intended orientation is cup-up, with vertical rails and slots.
Slicer behavior and physical fit require separate validation.

`rail_clearance` tunes the geometric fit while retaining an undercut.
"""

from dataclasses import dataclass, fields
from math import isfinite
from numbers import Real

import cadquery as cq

ModelParts = dict[str, cq.Workplane]


@dataclass(frozen=True)
class PixelGardenModuleParameters:
    """Dimensions for one dovetailed pixel cup."""

    size: float = 40.0
    height: float = 40.0
    wall: float = 2.0
    floor: float = 2.4
    drain_hole_diameter: float = 6.0
    corner_radius: float = 1.5

    rail_depth: float = 3.0
    rail_base_width: float = 6.0
    rail_tip_width: float = 9.0
    rail_clearance: float = 0.25
    rail_end_gap: float = 1.0

    @property
    def slot_wall(self) -> float:
        """Wall thickness on the slotted faces: the plain wall plus the
        material the slot is cut from."""
        return self.wall + self.rail_depth + self.rail_clearance

    @property
    def rail_height(self) -> float:
        return self.height - self.rail_end_gap

    @property
    def cavity_width(self) -> float:
        return self.size - self.wall - self.slot_wall

    def validate(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not isfinite(value)
            ):
                raise ValueError(f"{field.name} must be a finite real number")

        positive_values = {
            "size": self.size,
            "height": self.height,
            "wall": self.wall,
            "floor": self.floor,
            "rail_depth": self.rail_depth,
            "rail_base_width": self.rail_base_width,
            "rail_tip_width": self.rail_tip_width,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        for name, value in {
            "drain_hole_diameter": self.drain_hole_diameter,
            "corner_radius": self.corner_radius,
            "rail_clearance": self.rail_clearance,
            "rail_end_gap": self.rail_end_gap,
        }.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

        if self.rail_tip_width <= self.rail_base_width:
            raise ValueError("rail_tip_width must exceed rail_base_width")

        flank = (self.rail_tip_width - self.rail_base_width) / 2

        # The slot mouth must remain narrower than the male rail tip.
        # Otherwise the dovetail can withdraw sideways without retaining it.
        if self.rail_clearance >= flank:
            raise ValueError(
                "rail_clearance must be smaller than the dovetail undercut"
            )

        # The cavity has square corners. Larger exterior rounding would thin
        # its +X/+Y corner below the requested wall thickness (or breach it).
        if self.corner_radius > self.wall:
            raise ValueError("corner_radius must not exceed wall for a square cavity")

        if flank > self.rail_depth:
            raise ValueError(
                "dovetail flank is wider than rail_depth, which leaves the "
                "slot lips too thin; reduce rail_tip_width or deepen the rail"
            )

        if self.rail_tip_width + 2 * self.rail_clearance >= self.size - 2 * self.wall:
            raise ValueError("rail_tip_width does not fit within the module face")

        if self.cavity_width <= self.drain_hole_diameter:
            raise ValueError("drain_hole_diameter does not fit inside the cavity")

        if self.cavity_width < 10.0:
            raise ValueError("module is too small to hold soil; increase size")

        if self.floor >= self.height:
            raise ValueError("floor must be thinner than height")

        if self.rail_end_gap >= self.height:
            raise ValueError("rail_end_gap must be shorter than height")


def _dovetail_profile(
    parameters: PixelGardenModuleParameters,
    *,
    grow: float,
) -> list[tuple[float, float]]:
    """Trapezoid in (along-face, outward) coordinates with the narrow
    base on the wall at 0 and the wide tip at `rail_depth`. `grow`
    pads every side for the slot."""
    base = parameters.rail_base_width / 2 + grow
    tip = parameters.rail_tip_width / 2 + grow
    depth = parameters.rail_depth + grow

    return [(-base, 0.0), (base, 0.0), (tip, depth), (-tip, depth)]


def _rail_on_x(
    parameters: PixelGardenModuleParameters,
    *,
    face_x: float,
    direction: float,
    grow: float,
    height: float,
    base_z: float,
) -> cq.Workplane:
    """Dovetail prism attached to the face at `face_x`, pointing
    outward along `direction` (+1 or -1), extruded upward in Z."""
    profile = [
        (face_x + direction * outward, along)
        for along, outward in _dovetail_profile(parameters, grow=grow)
    ]

    return (
        cq.Workplane("XY")
        .workplane(offset=base_z)
        .polyline(profile)
        .close()
        .extrude(height)
    )


def _rail_on_y(
    parameters: PixelGardenModuleParameters,
    *,
    face_y: float,
    direction: float,
    grow: float,
    height: float,
    base_z: float,
) -> cq.Workplane:
    profile = [
        (along, face_y + direction * outward)
        for along, outward in _dovetail_profile(parameters, grow=grow)
    ]

    return (
        cq.Workplane("XY")
        .workplane(offset=base_z)
        .polyline(profile)
        .close()
        .extrude(height)
    )


def build_module(
    parameters: PixelGardenModuleParameters,
) -> cq.Workplane:
    """One cup with rails on +X/+Y and slots on -X/-Y."""
    parameters.validate()
    half = parameters.size / 2

    body = cq.Workplane("XY").box(
        parameters.size,
        parameters.size,
        parameters.height,
        centered=(True, True, False),
    )

    if parameters.corner_radius > 0:
        body = body.edges("|Z").fillet(parameters.corner_radius)

    # Cavity is offset by the plain wall on the rail faces and by the
    # thicker slot wall on the slotted faces.
    cavity_min = -half + parameters.slot_wall
    cavity_max = half - parameters.wall
    cavity = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor)
        .center(
            (cavity_min + cavity_max) / 2,
            (cavity_min + cavity_max) / 2,
        )
        .rect(parameters.cavity_width, parameters.cavity_width)
        .extrude(parameters.height)
    )
    body = body.cut(cavity)

    if parameters.drain_hole_diameter > 0:
        margin = 0.5
        hole = (
            cq.Workplane("XY")
            .workplane(offset=-margin)
            .center(
                (cavity_min + cavity_max) / 2,
                (cavity_min + cavity_max) / 2,
            )
            .circle(parameters.drain_hole_diameter / 2)
            .extrude(parameters.floor + 2 * margin)
        )
        body = body.cut(hole)

    rail_kwargs = {
        "grow": 0.0,
        "height": parameters.rail_height,
        "base_z": 0.0,
    }
    body = body.union(
        _rail_on_x(parameters, face_x=half, direction=1.0, **rail_kwargs)
    ).union(_rail_on_y(parameters, face_y=half, direction=1.0, **rail_kwargs))

    # Slots run the full height plus a margin so they are open top and
    # bottom; the neighbour's rail slides in from above.
    margin = 0.5
    slot_kwargs = {
        "grow": parameters.rail_clearance,
        "height": parameters.height + 2 * margin,
        "base_z": -margin,
    }
    body = body.cut(
        _rail_on_x(parameters, face_x=-half, direction=1.0, **slot_kwargs)
    ).cut(_rail_on_y(parameters, face_y=-half, direction=1.0, **slot_kwargs))

    # Wide/deep slots can intersect and cut an isolated corner off the cup
    # even when each individual parameter passes the analytic constraints.
    solids = body.solids().vals()
    if len(solids) != 1 or not solids[0].isValid():
        raise ValueError("rail/slot geometry must leave one valid connected solid")
    volume = solids[0].Volume()
    if not isfinite(volume) or volume <= 0:
        raise ValueError("module must have finite positive volume")
    return body


def build_pixel_garden_module(
    parameters: PixelGardenModuleParameters,
) -> ModelParts:
    """Build one module; print as many as the picture needs."""
    return {"main": build_module(parameters)}
