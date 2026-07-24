"""Canonical Gridfinity dimensions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GridfinitySpecification:
    """Standard Gridfinity sizing."""

    grid_size: float = 42.0
    base_height: float = 7.0
    clearance: float = 0.5

    def cell_width(
        self,
        cells: int,
    ) -> float:
        if cells <= 0:
            raise ValueError("cells must be greater than zero")

        return cells * self.grid_size - self.clearance

    def cell_depth(
        self,
        cells: int,
    ) -> float:
        return self.cell_width(cells)
