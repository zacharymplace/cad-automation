"""Heat-set insert board-fastening backend."""

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
    InsertBossParameters,
    add_heat_set_insert_boss,
)
from zcad_core.hardware import get_fastener

from zcad.fastening.artifacts import (
    BoardFasteningArtifacts,
)
from zcad.fastening.verification import (
    BoardFasteningBuild,
    analyze_heat_set_insert_fit,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
)


class HeatSetInsertPolicy(Protocol):
    """Policy fields required to derive heat-set insert bosses."""

    board_fastener: str | None
    insert_boss_radial_wall_mm: float


def derive_board_insert_boss_parameters(
    *,
    assembly: DeviceAssembly,
    specification: EnclosureSpecification,
    enclosure_parameters: EnclosureParameters,
    policy: HeatSetInsertPolicy,
) -> tuple[InsertBossParameters, ...]:
    """Derive heat-set insert bosses from board mounting metadata."""
    if policy.board_fastener is None:
        raise ValueError("board_fastener is required for heat-set insert fastening")

    board = assembly.get("board")
    positions = assembly_mounting_hole_positions(board)

    if not positions:
        return ()

    fastener = get_fastener(policy.board_fastener)
    body_bottom_z_mm = -enclosure_parameters.height / 2

    derived: list[InsertBossParameters] = []

    for (
        world_x_mm,
        world_y_mm,
        board_bottom_z_mm,
    ) in positions:
        boss_height_mm = board_bottom_z_mm - specification.bottom_z_mm

        if boss_height_mm <= 0:
            raise ValueError(
                "board mounting position must be above the enclosure cavity floor"
            )

        parameters = InsertBossParameters.from_fastener(
            fastener=fastener,
            x=(world_x_mm - specification.center_x_mm),
            y=(world_y_mm - specification.center_y_mm),
            base_height_mm=(enclosure_parameters.floor),
            base_z_mm=body_bottom_z_mm,
            boss_height_mm=boss_height_mm,
            radial_wall_mm=(policy.insert_boss_radial_wall_mm),
        )
        parameters.validate()
        derived.append(parameters)

    return tuple(derived)


def add_board_insert_bosses(
    *,
    body: cq.Workplane,
    parameters: tuple[
        InsertBossParameters,
        ...,
    ],
) -> cq.Workplane:
    """Add all derived heat-set insert bosses."""
    result = body

    for insert_boss in parameters:
        result = add_heat_set_insert_boss(
            result,
            parameters=insert_boss,
        )

    return result


@dataclass(frozen=True)
class HeatSetInsertBackend:
    """Backend for heat-set insert PCB bosses."""

    strategy: object = "heat_set_insert"

    def derive(
        self,
        *,
        assembly: DeviceAssembly,
        specification: EnclosureSpecification,
        enclosure_parameters: EnclosureParameters,
        policy: object,
    ) -> BoardFasteningArtifacts:
        """Derive heat-set insert artifacts."""
        return BoardFasteningArtifacts(
            insert_boss_parameters=(
                derive_board_insert_boss_parameters(
                    assembly=assembly,
                    specification=specification,
                    enclosure_parameters=(enclosure_parameters),
                    policy=cast(
                        HeatSetInsertPolicy,
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
        """Apply heat-set insert boss geometry."""
        if artifacts.standoff_parameters:
            raise ValueError("heat-set insert backend received standoff geometry")

        return add_board_insert_bosses(
            body=body,
            parameters=(artifacts.insert_boss_parameters),
        )

    def analyze_fit(
        self,
        *,
        build: BoardFasteningBuild,
        tolerance_mm: float,
    ) -> tuple[InterferenceFinding, ...]:
        """Verify generated board-fastening geometry."""
        return analyze_heat_set_insert_fit(
            build,
            tolerance_mm=tolerance_mm,
        )
