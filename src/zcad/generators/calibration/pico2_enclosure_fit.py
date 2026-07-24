"""Two-part Raspberry Pi Pico 2 enclosure fit-test assembly."""

from dataclasses import dataclass

import cadquery as cq
from zcad_core.features import (
    ConnectorCutoutParameters,
    add_board_standoffs,
    cut_connector_opening,
)
from zcad_core.features.labels import (
    add_embossed_label,
)
from zcad_core.hardware import (
    get_raspberry_pi_pico2,
)


@dataclass(frozen=True)
class Pico2EnclosureFitParameters:
    """Parameters for a Pico 2 enclosure and fitted lid."""

    wall_mm: float = 2.0
    floor_mm: float = 2.0
    internal_height_mm: float = 8.0
    board_clearance_mm: float = 2.0

    standoff_height_mm: float = 3.0
    standoff_radial_wall_mm: float = 1.5
    mounting_hole_clearance_mm: float = 0.5

    lid_thickness_mm: float = 2.0
    lid_clearance_mm: float = 0.25
    lid_lip_height_mm: float = 2.5
    lid_lip_wall_mm: float = 1.2

    usb_width_clearance_mm: float = 0.6
    usb_height_clearance_mm: float = 0.6

    label_text: str = "PICO 2"
    label_size_mm: float = 5.0
    label_height_mm: float = 0.5

    def validate(self) -> None:
        """Validate enclosure geometry."""
        positive_values = {
            "wall_mm": self.wall_mm,
            "floor_mm": self.floor_mm,
            "internal_height_mm": (self.internal_height_mm),
            "board_clearance_mm": (self.board_clearance_mm),
            "standoff_height_mm": (self.standoff_height_mm),
            "standoff_radial_wall_mm": (self.standoff_radial_wall_mm),
            "lid_thickness_mm": (self.lid_thickness_mm),
            "lid_lip_height_mm": (self.lid_lip_height_mm),
            "lid_lip_wall_mm": (self.lid_lip_wall_mm),
            "label_size_mm": self.label_size_mm,
            "label_height_mm": (self.label_height_mm),
        }

        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        nonnegative_values = {
            "mounting_hole_clearance_mm": (self.mounting_hole_clearance_mm),
            "lid_clearance_mm": (self.lid_clearance_mm),
            "usb_width_clearance_mm": (self.usb_width_clearance_mm),
            "usb_height_clearance_mm": (self.usb_height_clearance_mm),
        }

        for name, value in nonnegative_values.items():
            if value < 0:
                raise ValueError(f"{name} must not be negative")

        if not self.label_text.strip():
            raise ValueError("label_text must not be empty")


def _resolved_dimensions(
    parameters: Pico2EnclosureFitParameters,
) -> tuple[float, float, float, float]:
    """Return outer width, depth, height, and inner width."""
    board = get_raspberry_pi_pico2()

    inner_width_mm = board.board_width_mm + (2 * parameters.board_clearance_mm)
    inner_depth_mm = board.board_length_mm + (2 * parameters.board_clearance_mm)

    outer_width_mm = inner_width_mm + (2 * parameters.wall_mm)
    outer_depth_mm = inner_depth_mm + (2 * parameters.wall_mm)
    outer_height_mm = parameters.floor_mm + parameters.internal_height_mm

    return (
        outer_width_mm,
        outer_depth_mm,
        outer_height_mm,
        inner_width_mm,
    )


def _build_body(
    parameters: Pico2EnclosureFitParameters,
) -> cq.Workplane:
    """Build the open enclosure body."""
    board = get_raspberry_pi_pico2()

    (
        outer_width_mm,
        outer_depth_mm,
        outer_height_mm,
        _,
    ) = _resolved_dimensions(parameters)

    inner_width_mm = outer_width_mm - (2 * parameters.wall_mm)
    inner_depth_mm = outer_depth_mm - (2 * parameters.wall_mm)

    body = cq.Workplane("XY").box(
        outer_width_mm,
        outer_depth_mm,
        outer_height_mm,
        centered=(True, True, False),
    )

    cavity = (
        cq.Workplane("XY")
        .workplane(
            offset=parameters.floor_mm,
        )
        .box(
            inner_width_mm,
            inner_depth_mm,
            parameters.internal_height_mm + 0.5,
            centered=(True, True, False),
        )
    )

    body = body.cut(cavity)

    body = add_board_standoffs(
        body,
        board=board,
        base_height_mm=parameters.floor_mm,
        standoff_height_mm=(parameters.standoff_height_mm),
        radial_wall_mm=(parameters.standoff_radial_wall_mm),
        hole_clearance_mm=(parameters.mounting_hole_clearance_mm),
    )

    board_top_z_mm = (
        parameters.floor_mm + parameters.standoff_height_mm + board.board_thickness_mm
    )

    cutout_parameters = ConnectorCutoutParameters.from_connector(
        connector=board.usb_connector,
        board_top_z_mm=board_top_z_mm,
        width_clearance_mm=(parameters.usb_width_clearance_mm),
        height_clearance_mm=(parameters.usb_height_clearance_mm),
        cutter_depth_mm=(parameters.wall_mm + 2.0),
    )

    return cut_connector_opening(
        body,
        parameters=cutout_parameters,
    )


def _build_lid(
    parameters: Pico2EnclosureFitParameters,
) -> cq.Workplane:
    """Build a fitted lid with an internal locating lip."""
    (
        outer_width_mm,
        outer_depth_mm,
        _,
        _,
    ) = _resolved_dimensions(parameters)

    inner_width_mm = outer_width_mm - (2 * parameters.wall_mm)
    inner_depth_mm = outer_depth_mm - (2 * parameters.wall_mm)

    lip_outer_width_mm = inner_width_mm - (2 * parameters.lid_clearance_mm)
    lip_outer_depth_mm = inner_depth_mm - (2 * parameters.lid_clearance_mm)

    lip_inner_width_mm = lip_outer_width_mm - (2 * parameters.lid_lip_wall_mm)
    lip_inner_depth_mm = lip_outer_depth_mm - (2 * parameters.lid_lip_wall_mm)

    if lip_inner_width_mm <= 0:
        raise ValueError("lid lip leaves no internal width")

    if lip_inner_depth_mm <= 0:
        raise ValueError("lid lip leaves no internal depth")

    lid_plate = cq.Workplane("XY").box(
        outer_width_mm,
        outer_depth_mm,
        parameters.lid_thickness_mm,
        centered=(True, True, False),
    )

    lip_outer = (
        cq.Workplane("XY")
        .workplane(
            offset=parameters.lid_thickness_mm,
        )
        .box(
            lip_outer_width_mm,
            lip_outer_depth_mm,
            parameters.lid_lip_height_mm,
            centered=(True, True, False),
        )
    )

    lip_inner = (
        cq.Workplane("XY")
        .workplane(
            offset=parameters.lid_thickness_mm,
        )
        .box(
            lip_inner_width_mm,
            lip_inner_depth_mm,
            parameters.lid_lip_height_mm + 0.5,
            centered=(True, True, False),
        )
    )

    lid = lid_plate.union(lip_outer.cut(lip_inner))

    return add_embossed_label(
        lid,
        text=parameters.label_text,
        x=0.0,
        y=0.0,
        base_height=parameters.lid_thickness_mm,
        text_size=parameters.label_size_mm,
        emboss_height=parameters.label_height_mm,
    )


def build_pico2_enclosure_fit(
    parameters: Pico2EnclosureFitParameters,
) -> dict[str, cq.Workplane]:
    """Build the Pico 2 enclosure body and fitted lid."""
    parameters.validate()

    return {
        "body": _build_body(parameters),
        "lid": _build_lid(parameters),
    }
