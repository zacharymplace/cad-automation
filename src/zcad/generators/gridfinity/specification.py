"""Canonical Gridfinity-inspired specification.

NOTE:
Only values with stable, corroborated references are included here.
Compatibility geometry (mating profile, stacking lip, etc.) is added
incrementally as it is validated.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GridfinitySpecification:
    """Shared Gridfinity dimensions."""

    # Horizontal system
    grid_pitch: float = 42.0
    bin_spacing: float = 0.5

    # Vertical sizing
    height_unit: float = 7.0

    # Verified profile values
    profile_corner_radius: float = 4.0
    bin_mating_depth: float = 4.75
    baseplate_mating_depth: float = 4.4

    bin_mating_inset: float = 2.4
    baseplate_mating_inset: float = 2.15

    bottom_chamfer: float = 0.8

    # Hardware
    magnet_diameter: float = 6.0
    magnet_depth: float = 2.0
    magnet_center_inset: float = 8.0

    screw_size: str = "M3"

    def cell_width(
        self,
        cells: int,
    ) -> float:
        if cells <= 0:
            raise ValueError("cells must be greater than zero")

        return cells * self.grid_pitch - self.bin_spacing

    def cell_depth(
        self,
        cells: int,
    ) -> float:
        return self.cell_width(cells)

    def height(
        self,
        units: int,
    ) -> float:
        if units <= 0:
            raise ValueError("units must be greater than zero")

        return units * self.height_unit
