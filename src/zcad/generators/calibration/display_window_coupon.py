"""Display-window and bezel calibration coupon."""

from dataclasses import dataclass

import cadquery as cq
from zcad_core.features import (
    DisplayBezelParameters,
    DisplayWindowParameters,
    add_display_bezel,
    cut_display_window,
)
from zcad_core.features.labels import (
    add_embossed_label,
)
from zcad_core.hardware import (
    get_reference_oled_128x64,
)


@dataclass(frozen=True)
class DisplayWindowCouponParameters:
    """Parameters for a display-window calibration coupon."""

    clearances_mm: tuple[float, ...] = (
        0.2,
        0.4,
        0.6,
    )

    cell_width_mm: float = 34.0
    panel_depth_mm: float = 32.0
    panel_thickness_mm: float = 2.0
    edge_margin_mm: float = 3.0

    window_center_y_mm: float = 4.0
    window_corner_radius_mm: float = 1.0

    bezel_wall_mm: float = 1.5
    bezel_height_mm: float = 0.8

    label_size_mm: float = 3.0
    label_height_mm: float = 0.4
    label_y_mm: float = -10.5

    def validate(self) -> None:
        """Validate coupon parameters."""
        if not self.clearances_mm:
            raise ValueError("clearances_mm must not be empty")

        for clearance_mm in self.clearances_mm:
            if clearance_mm < 0:
                raise ValueError("clearances_mm values must not be negative")

        positive_values = {
            "cell_width_mm": self.cell_width_mm,
            "panel_depth_mm": self.panel_depth_mm,
            "panel_thickness_mm": (self.panel_thickness_mm),
            "edge_margin_mm": self.edge_margin_mm,
            "bezel_wall_mm": self.bezel_wall_mm,
            "bezel_height_mm": self.bezel_height_mm,
            "label_size_mm": self.label_size_mm,
            "label_height_mm": self.label_height_mm,
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.window_corner_radius_mm < 0:
            raise ValueError("window_corner_radius_mm must not be negative")

        display = get_reference_oled_128x64()
        largest_clearance_mm = max(self.clearances_mm)

        largest_opening_width_mm = display.active_width_mm + (2 * largest_clearance_mm)
        largest_bezel_width_mm = largest_opening_width_mm + (2 * self.bezel_wall_mm)

        usable_cell_width_mm = self.cell_width_mm - (2 * self.edge_margin_mm)

        if largest_bezel_width_mm > usable_cell_width_mm:
            raise ValueError("display bezel does not fit within cell_width_mm")

        largest_opening_height_mm = display.active_height_mm + (
            2 * largest_clearance_mm
        )
        largest_bezel_height_mm = largest_opening_height_mm + (2 * self.bezel_wall_mm)

        half_panel_depth_mm = self.panel_depth_mm / 2

        bezel_top_y_mm = self.window_center_y_mm + (largest_bezel_height_mm / 2)

        if bezel_top_y_mm > half_panel_depth_mm - self.edge_margin_mm:
            raise ValueError("display bezel does not fit within panel_depth_mm")

        label_bottom_y_mm = self.label_y_mm - (self.label_size_mm / 2)

        if label_bottom_y_mm < -half_panel_depth_mm + self.edge_margin_mm:
            raise ValueError("display label does not fit within panel_depth_mm")

    @property
    def panel_width_mm(self) -> float:
        """Return total coupon width."""
        return len(self.clearances_mm) * self.cell_width_mm


def _cell_center_x_mm(
    *,
    index: int,
    count: int,
    cell_width_mm: float,
) -> float:
    """Return the centered X position for one cell."""
    first_center_x_mm = -((count - 1) * cell_width_mm) / 2

    return first_center_x_mm + (index * cell_width_mm)


def build_display_window_coupon(
    parameters: DisplayWindowCouponParameters,
) -> cq.Workplane:
    """Build a labeled display-window clearance coupon."""
    parameters.validate()

    display = get_reference_oled_128x64()

    model = cq.Workplane("XY").box(
        parameters.panel_width_mm,
        parameters.panel_depth_mm,
        parameters.panel_thickness_mm,
        centered=(True, True, False),
    )

    clearance_values = tuple(parameters.clearances_mm)

    for index, clearance_mm in enumerate(clearance_values):
        center_x_mm = _cell_center_x_mm(
            index=index,
            count=len(clearance_values),
            cell_width_mm=parameters.cell_width_mm,
        )

        window = DisplayWindowParameters.from_display(
            display=display,
            panel_base_z_mm=0.0,
            panel_thickness_mm=(parameters.panel_thickness_mm),
            x=center_x_mm,
            y=parameters.window_center_y_mm,
            window_clearance_mm=clearance_mm,
            corner_radius_mm=(parameters.window_corner_radius_mm),
        )

        model = cut_display_window(
            model,
            parameters=window,
        )

        bezel = DisplayBezelParameters.from_window(
            window=window,
            bezel_wall_mm=(parameters.bezel_wall_mm),
            bezel_height_mm=(parameters.bezel_height_mm),
        )

        model = add_display_bezel(
            model,
            parameters=bezel,
        )

        model = add_embossed_label(
            model,
            text=f"{clearance_mm:.1f}",
            x=center_x_mm,
            y=parameters.label_y_mm,
            base_height=(parameters.panel_thickness_mm),
            text_size=parameters.label_size_mm,
            emboss_height=(parameters.label_height_mm),
        )

    return model
