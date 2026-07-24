"""Raspberry Pi Pico 2 mounting calibration coupon."""

from dataclasses import dataclass

import cadquery as cq
from zcad_core.features import (
    add_board_standoffs,
)
from zcad_core.features.labels import (
    add_embossed_label,
)
from zcad_core.hardware import (
    get_raspberry_pi_pico2,
)


@dataclass(frozen=True)
class Pico2MountCouponParameters:
    """Parameters for a Raspberry Pi Pico 2 mounting coupon."""

    board_edge_clearance_mm: float = 5.0
    base_height_mm: float = 2.0
    standoff_height_mm: float | None = None
    standoff_radial_wall_mm: float = 1.5
    mounting_hole_clearance_mm: float | None = None
    label_text: str = "PICO 2"
    label_size_mm: float = 4.0
    emboss_height_mm: float = 0.5

    def validate(self) -> None:
        """Validate coupon parameters."""
        positive_values = {
            "board_edge_clearance_mm": (self.board_edge_clearance_mm),
            "base_height_mm": self.base_height_mm,
            "standoff_radial_wall_mm": (self.standoff_radial_wall_mm),
            "label_size_mm": self.label_size_mm,
            "emboss_height_mm": self.emboss_height_mm,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.standoff_height_mm is not None and self.standoff_height_mm <= 0:
            raise ValueError("standoff_height_mm must be greater than zero")

        if (
            self.mounting_hole_clearance_mm is not None
            and self.mounting_hole_clearance_mm < 0
        ):
            raise ValueError("mounting_hole_clearance_mm must not be negative")

        if not self.label_text.strip():
            raise ValueError("label_text must not be empty")


def build_pico2_mount_coupon(
    parameters: Pico2MountCouponParameters,
) -> cq.Workplane:
    """Build a printable Pico 2 board-mount calibration plate."""
    parameters.validate()

    board = get_raspberry_pi_pico2()

    width_mm = board.board_width_mm + (2 * parameters.board_edge_clearance_mm)
    depth_mm = board.board_length_mm + (2 * parameters.board_edge_clearance_mm)

    model = cq.Workplane("XY").box(
        width_mm,
        depth_mm,
        parameters.base_height_mm,
        centered=(True, True, False),
    )

    model = add_board_standoffs(
        model,
        board=board,
        base_height_mm=parameters.base_height_mm,
        standoff_height_mm=parameters.standoff_height_mm,
        radial_wall_mm=parameters.standoff_radial_wall_mm,
        hole_clearance_mm=(parameters.mounting_hole_clearance_mm),
    )

    label_y = board.mounting_hole_spacing_y_mm / 2 - 5.0

    return add_embossed_label(
        model,
        text=parameters.label_text,
        x=0.0,
        y=label_y,
        base_height=parameters.base_height_mm,
        text_size=parameters.label_size_mm,
        emboss_height=parameters.emboss_height_mm,
    )
