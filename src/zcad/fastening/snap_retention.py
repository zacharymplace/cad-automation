"""Snap-retention board-fastening artifacts and contracts."""

from dataclasses import dataclass
from typing import Protocol


class SnapRetentionPolicy(Protocol):
    """Policy fields required to derive snap-retention features."""

    snap_clip_wall_mm: float
    snap_clip_height_mm: float
    snap_clip_overhang_mm: float
    snap_clip_clearance_mm: float
    snap_clip_flex_length_mm: float


@dataclass(frozen=True)
class SnapRetentionParameters:
    """Geometry parameters for one printed board-retention clip."""

    x: float
    y: float

    width_mm: float
    wall_mm: float
    height_mm: float
    overhang_mm: float
    clearance_mm: float
    flex_length_mm: float

    base_z_mm: float
    rotation_degrees: float = 0.0

    def validate(self) -> None:
        """Validate one snap-retention feature."""
        positive_values = {
            "width_mm": self.width_mm,
            "wall_mm": self.wall_mm,
            "height_mm": self.height_mm,
            "overhang_mm": self.overhang_mm,
            "flex_length_mm": self.flex_length_mm,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.clearance_mm < 0:
            raise ValueError("clearance_mm must not be negative")
