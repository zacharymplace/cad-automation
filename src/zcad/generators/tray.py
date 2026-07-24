"""Parametric open-top tray."""

from dataclasses import dataclass

import cadquery as cq


@dataclass(frozen=True)
class TrayParameters:
    width: float
    depth: float
    height: float
    wall: float = 3.0
    floor: float = 3.0
    corner_radius: float = 4.0

    def validate(self) -> None:
        values = {
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "wall": self.wall,
            "floor": self.floor,
        }

        for name, value in values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.corner_radius < 0:
            raise ValueError("corner_radius cannot be negative")

        if self.width <= self.wall * 2:
            raise ValueError("width must exceed twice the wall thickness")

        if self.depth <= self.wall * 2:
            raise ValueError("depth must exceed twice the wall thickness")

        if self.height <= self.floor:
            raise ValueError("height must exceed floor thickness")


def build_tray(
    parameters: TrayParameters,
) -> cq.Workplane:
    parameters.validate()

    outer = cq.Workplane("XY").box(
        parameters.width,
        parameters.depth,
        parameters.height,
    )

    inner = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor)
        .box(
            parameters.width - 2 * parameters.wall,
            parameters.depth - 2 * parameters.wall,
            parameters.height - parameters.floor,
            centered=(True, True, False),
        )
    )

    model = outer.cut(inner)

    if parameters.corner_radius > 0:
        model = model.edges("|Z").fillet(parameters.corner_radius)

    return model
