"""Reusable board-fastening verification contracts."""

from typing import Protocol, runtime_checkable

from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureSpecification,
)
from zcad_core.features import (
    InsertBossParameters,
    PcbStandoffParameters,
)

from zcad.generators.enclosure import (
    EnclosureParameters,
)


@runtime_checkable
class BoardFasteningVerificationPolicy(Protocol):
    """Policy fields required for fastening verification."""

    standoff_radial_wall_mm: float
    standoff_hole_clearance_mm: float | None

    board_fastener: str | None
    insert_boss_radial_wall_mm: float


@runtime_checkable
class BoardFasteningBuild(Protocol):
    """Build data required to verify board fastening."""

    assembly: DeviceAssembly
    specification: EnclosureSpecification
    enclosure_parameters: EnclosureParameters
    policy: BoardFasteningVerificationPolicy

    standoff_parameters: tuple[
        PcbStandoffParameters,
        ...,
    ]
    insert_boss_parameters: tuple[
        InsertBossParameters,
        ...,
    ]
