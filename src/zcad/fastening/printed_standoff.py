"""Printed-standoff fastening backend."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, cast

import cadquery as cq
from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureSpecification,
    InterferenceFinding,
    assembly_mounting_hole_positions,
)
from zcad_core.features import (
    PcbStandoffParameters,
    add_pcb_standoff,
)

from zcad.fastening.artifacts import (
    BoardFasteningArtifacts,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
)


class PrintedStandoffPolicy(Protocol):
    """Policy fields required to derive printed PCB standoffs."""

    standoff_radial_wall_mm: float
    standoff_hole_clearance_mm: float | None


DeriveCallback = Callable[..., BoardFasteningArtifacts]
ApplyCallback = Callable[
    [cq.Workplane, BoardFasteningArtifacts],
    cq.Workplane,
]
FitCallback = Callable[
    [object, float],
    tuple[InterferenceFinding, ...],
]


def derive_board_standoff_parameters(
    *,
    assembly: DeviceAssembly,
    specification: EnclosureSpecification,
    enclosure_parameters: EnclosureParameters,
    policy: PrintedStandoffPolicy,
) -> tuple[PcbStandoffParameters, ...]:
    """Derive enclosure-local standoffs from board mounting metadata."""
    board = assembly.get("board")
    positions = assembly_mounting_hole_positions(board)

    if not positions:
        return ()

    mounting = board.metadata.get("mounting")

    if not isinstance(mounting, dict):
        raise TypeError("board mounting metadata must be a dictionary")

    hole_diameter_mm = mounting.get("hole_diameter_mm")
    recommended_clearance_mm = mounting.get("recommended_clearance_mm")

    if not isinstance(
        hole_diameter_mm,
        int | float,
    ):
        raise TypeError("board mounting hole diameter must be numeric")

    if not isinstance(
        recommended_clearance_mm,
        int | float,
    ):
        raise TypeError("board mounting clearance must be numeric")

    resolved_clearance_mm = (
        policy.standoff_hole_clearance_mm
        if policy.standoff_hole_clearance_mm is not None
        else recommended_clearance_mm
    )

    hole_with_clearance_mm = hole_diameter_mm + resolved_clearance_mm
    outer_diameter_mm = hole_with_clearance_mm + 2 * policy.standoff_radial_wall_mm

    body_bottom_z_mm = -enclosure_parameters.height / 2

    derived: list[PcbStandoffParameters] = []

    for (
        world_x_mm,
        world_y_mm,
        board_bottom_z_mm,
    ) in positions:
        standoff_height_mm = board_bottom_z_mm - specification.bottom_z_mm

        if standoff_height_mm <= 0:
            raise ValueError(
                "board mounting position must be above the enclosure cavity floor"
            )

        parameters = PcbStandoffParameters(
            x=(world_x_mm - specification.center_x_mm),
            y=(world_y_mm - specification.center_y_mm),
            base_height_mm=(enclosure_parameters.floor),
            standoff_height_mm=(standoff_height_mm),
            outer_diameter_mm=(outer_diameter_mm),
            hole_diameter_mm=(hole_with_clearance_mm),
            base_z_mm=body_bottom_z_mm,
        )
        parameters.validate()
        derived.append(parameters)

    return tuple(derived)


def add_board_standoffs(
    *,
    body: cq.Workplane,
    parameters: tuple[
        PcbStandoffParameters,
        ...,
    ],
) -> cq.Workplane:
    """Add all derived PCB standoffs to an enclosure body."""
    result = body

    for standoff in parameters:
        result = add_pcb_standoff(
            result,
            parameters=standoff,
        )

    return result


@dataclass(frozen=True)
class PrintedStandoffBackend:
    """Backend for printed PCB standoffs."""

    strategy: object = "printed_standoff"
    derive_callback: DeriveCallback | None = None
    apply_callback: ApplyCallback | None = None
    fit_callback: FitCallback | None = None

    def derive(
        self,
        *,
        assembly: DeviceAssembly,
        specification: EnclosureSpecification,
        enclosure_parameters: EnclosureParameters,
        policy: object,
    ) -> BoardFasteningArtifacts:
        """Derive printed-standoff artifacts."""
        if self.derive_callback is not None:
            return self.derive_callback(
                assembly=assembly,
                specification=specification,
                enclosure_parameters=(enclosure_parameters),
                policy=policy,
            )

        return BoardFasteningArtifacts(
            standoff_parameters=(
                derive_board_standoff_parameters(
                    assembly=assembly,
                    specification=specification,
                    enclosure_parameters=(enclosure_parameters),
                    policy=cast(
                        PrintedStandoffPolicy,
                        policy,
                    ),
                )
            )
        )

    def apply(
        self,
        *,
        body: cq.Workplane,
        artifacts: BoardFasteningArtifacts,
    ) -> cq.Workplane:
        """Apply printed-standoff geometry."""
        if artifacts.insert_boss_parameters:
            raise ValueError("printed standoff backend received insert-boss geometry")

        if self.apply_callback is not None:
            return self.apply_callback(
                body,
                artifacts,
            )

        return add_board_standoffs(
            body=body,
            parameters=(artifacts.standoff_parameters),
        )

    def analyze_fit(
        self,
        *,
        build: object,
        tolerance_mm: float,
    ) -> tuple[InterferenceFinding, ...]:
        """Verify printed-standoff geometry."""
        if self.fit_callback is None:
            raise RuntimeError("printed standoff fit callback is not configured")

        return self.fit_callback(
            build,
            tolerance_mm,
        )
