"""Pico 2 enclosure fit-test artifact."""

from dataclasses import dataclass

import cadquery as cq
from zcad_core.features import (
    ConnectorCutoutParameters,
    add_board_standoffs,
    cut_connector_opening,
)
from zcad_core.hardware import (
    get_raspberry_pi_pico2,
)


@dataclass(frozen=True)
class Pico2EnclosureFitParameters:
    """Parameters for a Pico 2 enclosure fit test."""

    wall_mm: float = 2.0
    floor_mm: float = 2.0
    internal_height_mm: float = 8.0
    board_clearance_mm: float = 2.0
    standoff_height_mm: float = 3.0


def build_pico2_enclosure_fit(
    parameters: Pico2EnclosureFitParameters,
) -> cq.Workplane:
    """Build an open-top enclosure fit test."""

    board = get_raspberry_pi_pico2()

    outer_x = (
        board.board_width_mm
        + (2 * parameters.board_clearance_mm)
        + (2 * parameters.wall_mm)
    )

    outer_y = (
        board.board_length_mm
        + (2 * parameters.board_clearance_mm)
        + (2 * parameters.wall_mm)
    )

    outer_z = parameters.floor_mm + parameters.internal_height_mm

    enclosure = cq.Workplane("XY").box(
        outer_x,
        outer_y,
        outer_z,
        centered=(True, True, False),
    )

    cavity = (
        cq.Workplane("XY")
        .workplane(offset=parameters.floor_mm)
        .box(
            outer_x - (2 * parameters.wall_mm),
            outer_y - (2 * parameters.wall_mm),
            parameters.internal_height_mm + 0.1,
            centered=(True, True, False),
        )
    )

    enclosure = enclosure.cut(cavity)

    enclosure = add_board_standoffs(
        enclosure,
        board=board,
        base_height_mm=parameters.floor_mm,
        standoff_height_mm=parameters.standoff_height_mm,
    )

    cutout = ConnectorCutoutParameters.from_connector(
        connector=board.usb_connector,
        board_top_z_mm=(
            parameters.floor_mm
            + parameters.standoff_height_mm
            + board.board_thickness_mm
        ),
    )

    return cut_connector_opening(
        enclosure,
        parameters=cutout,
    )
