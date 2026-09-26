"""Pixel wall hook: a screw-mounted J-hook with a pixel relief on its face.

The profile is an L with an upturned lip, extruded to `width`: a wall
plate, an arm reaching out from its foot, and a lip at the end so a
headphone band or a coiled cable cannot slide off. Two countersunk
screw holes run through the plate near its top and bottom, and a
pixel pattern (an eighth note by default) is recessed into the front
face between them.

Print it lying on its side, profile flat on the bed: no supports,
and the layers run in the plane the load acts in, which is the
strong direction for a hook. The screw holes then print as
horizontal bores, which FDM manages at this diameter.
"""

from dataclasses import dataclass, field

import cadquery as cq

from zcad.generators.pixel_grid import PixelGrid

ModelParts = dict[str, cq.Workplane]

NOTE_PATTERN: tuple[str, ...] = (
    "....XX.",
    "....X.X",
    "....X.X",
    "....X..",
    "..XXX..",
    ".XXXX..",
    "..XX...",
)


@dataclass(frozen=True)
class PixelHookParameters:
    """Dimensions for the plate, arm, lip, holes, and relief."""

    width: float = 40.0
    plate_thickness: float = 4.0
    plate_height: float = 70.0
    arm_length: float = 30.0
    arm_thickness: float = 5.0
    lip_height: float = 12.0
    lip_thickness: float = 4.0
    corner_radius: float = 1.5

    screw_hole_diameter: float = 4.2
    countersink_diameter: float = 8.5
    hole_inset: float = 8.0

    pixel_size: float = 5.0
    pattern: tuple[str, ...] = field(default_factory=lambda: NOTE_PATTERN)
    relief_depth: float = 1.0
    pixel_inset: float = 0.2

    @property
    def grid(self) -> PixelGrid:
        return PixelGrid(rows=tuple(self.pattern), pixel_size=self.pixel_size)

    @property
    def reach(self) -> float:
        return self.plate_thickness + self.arm_length

    @property
    def hole_centers_z(self) -> tuple[float, float]:
        """Lower hole clears the arm; upper hole sits below the top edge."""
        radius = self.countersink_diameter / 2
        return (
            self.arm_thickness + self.hole_inset + radius,
            self.plate_height - self.hole_inset - radius,
        )

    @property
    def relief_center_z(self) -> float:
        low, high = self.hole_centers_z
        return (low + high) / 2

    def validate(self) -> None:
        for name, value in {
            "width": self.width,
            "plate_thickness": self.plate_thickness,
            "plate_height": self.plate_height,
            "arm_length": self.arm_length,
            "arm_thickness": self.arm_thickness,
            "lip_height": self.lip_height,
            "lip_thickness": self.lip_thickness,
            "screw_hole_diameter": self.screw_hole_diameter,
            "countersink_diameter": self.countersink_diameter,
            "pixel_size": self.pixel_size,
            "relief_depth": self.relief_depth,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        for name, value in {
            "corner_radius": self.corner_radius,
            "hole_inset": self.hole_inset,
            "pixel_inset": self.pixel_inset,
        }.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

        if self.countersink_diameter <= self.screw_hole_diameter:
            raise ValueError("countersink_diameter must exceed screw_hole_diameter")

        countersink_depth = (self.countersink_diameter - self.screw_hole_diameter) / 2

        if self.plate_thickness - countersink_depth < 1.2:
            raise ValueError("countersink is too deep for plate_thickness")

        if self.plate_thickness - self.relief_depth < 1.2:
            raise ValueError("relief_depth leaves less than 1.2mm of plate")

        if self.lip_thickness >= self.arm_length:
            raise ValueError("lip_thickness must be shorter than arm_length")

        if self.lip_height <= self.arm_thickness:
            raise ValueError("lip_height must rise above arm_thickness")

        if self.corner_radius >= min(self.plate_thickness, self.lip_thickness) / 2:
            raise ValueError(
                "corner_radius must be under half the plate and lip thickness"
            )

        if self.countersink_diameter >= self.width - 4.0:
            raise ValueError("countersink_diameter is too wide for width")

        low, high = self.hole_centers_z

        if high - low < self.countersink_diameter:
            raise ValueError("plate_height is too short for two screw holes")

        self.grid.validate_shape()

        if 2 * self.pixel_inset >= self.pixel_size:
            raise ValueError("pixel_inset is too large for pixel_size")

        if self.grid.width > self.width - 4.0:
            raise ValueError("pattern is wider than the plate")

        clear_span = (high - low) - self.countersink_diameter

        if self.grid.depth > clear_span:
            raise ValueError("pattern does not fit between the screw holes")


def _profile(parameters: PixelHookParameters) -> list[tuple[float, float]]:
    """(x outward from wall, z up) around the L-with-lip section."""
    pt = parameters.plate_thickness
    reach = parameters.reach
    lip_x = reach - parameters.lip_thickness

    return [
        (0.0, 0.0),
        (reach, 0.0),
        (reach, parameters.lip_height),
        (lip_x, parameters.lip_height),
        (lip_x, parameters.arm_thickness),
        (pt, parameters.arm_thickness),
        (pt, parameters.plate_height),
        (0.0, parameters.plate_height),
    ]


def _edges_at_height(z: float) -> cq.selectors.BoxSelector:
    """Select edges whose centre lies at height `z`."""
    return cq.selectors.BoxSelector((-1e4, -1e4, z - 1e-3), (1e4, 1e4, z + 1e-3))


def build_hook(
    parameters: PixelHookParameters,
) -> cq.Workplane:
    """Extruded profile with countersunk holes and a face relief."""
    half_width = parameters.width / 2

    # The XZ plane's normal points to -Y, so an offset of +half puts the
    # sketch at y = -half and a negative extrude runs it toward +Y,
    # centring the hook on the XZ plane.
    body = (
        cq.Workplane("XZ")
        .workplane(offset=half_width)
        .polyline(_profile(parameters))
        .close()
        .extrude(-parameters.width)
    )

    if parameters.corner_radius > 0:
        # Round only the convex top corners of the plate and the lip;
        # the back and bottom stay square against the wall.
        for z in (parameters.plate_height, parameters.lip_height):
            body = (
                body.edges("|Y")
                .edges(_edges_at_height(z))
                .fillet(parameters.corner_radius)
            )

    pt = parameters.plate_thickness
    margin = 0.5

    for z in parameters.hole_centers_z:
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=-margin)
            .center(0.0, z)
            .circle(parameters.screw_hole_diameter / 2)
            .extrude(pt + 2 * margin)
        )
        body = body.cut(bore)

        sink_radius = parameters.countersink_diameter / 2
        sink_depth = sink_radius - parameters.screw_hole_diameter / 2
        countersink = cq.Solid.makeCone(
            sink_radius + margin,
            parameters.screw_hole_diameter / 2,
            sink_depth + margin,
            cq.Vector(pt + margin, 0.0, z),
            cq.Vector(-1, 0, 0),
        )
        body = body.cut(cq.Workplane("XY").newObject([countersink]))

    grid = parameters.grid
    tile = parameters.pixel_size - 2 * parameters.pixel_inset
    depth = parameters.relief_depth + margin

    # Viewer stands at +X looking at the plate; their left is +Y.
    for pixel in sorted(grid.filled_pixels()):
        u, v = grid.pixel_center(pixel)
        recess = cq.Workplane("XY").box(depth, tile, tile)
        recess = recess.translate(
            (
                pt - parameters.relief_depth + depth / 2,
                -u,
                parameters.relief_center_z + v,
            )
        )
        body = body.cut(recess)

    return body


def build_pixel_hook(
    parameters: PixelHookParameters,
) -> ModelParts:
    """Build the single hook."""
    parameters.validate()

    return {"main": build_hook(parameters)}
