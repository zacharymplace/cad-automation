"""Snap-retention board-fastening artifacts and contracts."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from typing import Protocol, runtime_checkable

from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureSpecification,
)

from zcad.generators.enclosure import (
    EnclosureParameters,
)


@runtime_checkable
class SnapRetentionPolicy(Protocol):
    """Policy fields required to derive snap-retention features."""

    snap_clip_wall_mm: float
    snap_clip_height_mm: float
    snap_clip_overhang_mm: float
    snap_clip_clearance_mm: float


@dataclass(frozen=True)
class SnapRetentionParameters:
    """Geometry parameters for one printed board-retention clip."""

    x: float
    y: float

    base_height_mm: float
    support_height_mm: float
    board_thickness_mm: float

    width_mm: float
    wall_mm: float
    height_mm: float
    overhang_mm: float
    clearance_mm: float
    compliant_span_mm: float

    base_z_mm: float
    rotation_degrees: float = 0.0

    def validate(self) -> None:
        """Validate one snap-retention feature."""
        positive_values = {
            "base_height_mm": self.base_height_mm,
            "support_height_mm": self.support_height_mm,
            "board_thickness_mm": self.board_thickness_mm,
            "width_mm": self.width_mm,
            "wall_mm": self.wall_mm,
            "height_mm": self.height_mm,
            "overhang_mm": self.overhang_mm,
            "compliant_span_mm": self.compliant_span_mm,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.clearance_mm < 0:
            raise ValueError("clearance_mm must not be negative")


_EDGE_ROTATION_DEGREES = {
    "positive_x": 0.0,
    "positive_y": 90.0,
    "negative_x": 180.0,
    "negative_y": -90.0,
}


def _numeric_metadata_value(
    value: object,
    *,
    name: str,
) -> float:
    """Return one numeric metadata value."""
    if not isinstance(value, int | float):
        raise TypeError(f"{name} must be numeric")

    return float(value)


def _board_local_clip_position(
    *,
    edge: str,
    center_offset_mm: float,
    edge_clearance_mm: float,
    board_width_mm: float,
    board_depth_mm: float,
) -> tuple[float, float]:
    """Return a clip anchor in board-local coordinates."""
    if edge == "negative_x":
        return (
            -board_width_mm / 2 - edge_clearance_mm,
            center_offset_mm,
        )

    if edge == "positive_x":
        return (
            board_width_mm / 2 + edge_clearance_mm,
            center_offset_mm,
        )

    if edge == "negative_y":
        return (
            center_offset_mm,
            -board_depth_mm / 2 - edge_clearance_mm,
        )

    if edge == "positive_y":
        return (
            center_offset_mm,
            board_depth_mm / 2 + edge_clearance_mm,
        )

    raise ValueError(f"unsupported board retention clip edge: {edge}")


def _rotate_xy(
    *,
    x: float,
    y: float,
    rotation_degrees: float,
) -> tuple[float, float]:
    """Rotate one XY point around the origin."""
    angle = radians(rotation_degrees)

    return (
        x * cos(angle) - y * sin(angle),
        x * sin(angle) + y * cos(angle),
    )


def derive_snap_retention_parameters(
    *,
    assembly: DeviceAssembly,
    specification: EnclosureSpecification,
    enclosure_parameters: EnclosureParameters,
    policy: SnapRetentionPolicy,
) -> tuple[SnapRetentionParameters, ...]:
    """Derive enclosure-local clips from board-retention metadata."""
    board = assembly.get("board")
    retention = board.metadata.get("retention")

    if retention is None:
        return ()

    if not isinstance(retention, dict):
        raise TypeError("board retention metadata must be a dictionary")

    if board.placement.rotation_x_deg or board.placement.rotation_y_deg:
        raise ValueError("snap retention does not support board X or Y rotation")

    insertion_axis = retention.get("insertion_axis")

    if insertion_axis != "positive_z":
        raise ValueError("snap retention currently supports only positive_z insertion")

    board_thickness_mm = _numeric_metadata_value(
        retention.get("board_thickness_mm"),
        name="board retention board_thickness_mm",
    )

    if board_thickness_mm <= 0:
        raise ValueError("board retention board_thickness_mm must be greater than zero")

    body_bottom_z_mm = -enclosure_parameters.height / 2
    cavity_floor_z_mm = body_bottom_z_mm + enclosure_parameters.floor
    support_height_mm = board.placement.z_mm - cavity_floor_z_mm

    if support_height_mm <= 0:
        raise ValueError("board retention support height must be greater than zero")

    clip_regions = retention.get("clip_regions")

    if not isinstance(clip_regions, tuple):
        raise TypeError("board retention clip regions must be a tuple")

    board_bounds = board.geometry.val().BoundingBox()
    board_width_mm = board_bounds.xlen
    board_depth_mm = board_bounds.ylen

    derived: list[SnapRetentionParameters] = []

    for index, region in enumerate(
        clip_regions,
        start=1,
    ):
        if not isinstance(region, dict):
            raise TypeError(f"board retention clip region {index} must be a dictionary")

        edge = region.get("edge")

        if not isinstance(edge, str):
            raise TypeError(
                f"board retention clip region {index} edge must be a string"
            )

        try:
            edge_rotation_degrees = _EDGE_ROTATION_DEGREES[edge]
        except KeyError as error:
            raise ValueError(
                f"unsupported board retention clip edge: {edge}"
            ) from error

        center_offset_mm = _numeric_metadata_value(
            region.get("center_offset_mm"),
            name=(f"board retention clip region {index} center_offset_mm"),
        )
        width_mm = _numeric_metadata_value(
            region.get("width_mm"),
            name=(f"board retention clip region {index} width_mm"),
        )
        edge_clearance_mm = _numeric_metadata_value(
            region.get("edge_clearance_mm"),
            name=(f"board retention clip region {index} edge_clearance_mm"),
        )

        if edge_clearance_mm < 0:
            raise ValueError(
                "board retention clip region "
                f"{index} edge_clearance_mm "
                "must not be negative"
            )

        local_x, local_y = _board_local_clip_position(
            edge=edge,
            center_offset_mm=center_offset_mm,
            edge_clearance_mm=edge_clearance_mm,
            board_width_mm=board_width_mm,
            board_depth_mm=board_depth_mm,
        )

        rotated_x, rotated_y = _rotate_xy(
            x=local_x,
            y=local_y,
            rotation_degrees=(board.placement.rotation_z_deg),
        )

        world_x = rotated_x + board.placement.x_mm
        world_y = rotated_y + board.placement.y_mm

        parameters = SnapRetentionParameters(
            x=world_x - specification.center_x_mm,
            y=world_y - specification.center_y_mm,
            base_height_mm=enclosure_parameters.floor,
            support_height_mm=support_height_mm,
            board_thickness_mm=board_thickness_mm,
            width_mm=width_mm,
            wall_mm=policy.snap_clip_wall_mm,
            height_mm=policy.snap_clip_height_mm,
            overhang_mm=policy.snap_clip_overhang_mm,
            clearance_mm=(policy.snap_clip_clearance_mm),
            compliant_span_mm=(
                support_height_mm + board_thickness_mm + policy.snap_clip_clearance_mm
            ),
            base_z_mm=body_bottom_z_mm,
            rotation_degrees=(edge_rotation_degrees + board.placement.rotation_z_deg),
        )
        parameters.validate()
        derived.append(parameters)

    return tuple(derived)
