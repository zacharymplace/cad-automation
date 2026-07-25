"""Derived artifacts produced by board-fastening backends."""

from dataclasses import dataclass

from zcad_core.features import (
    InsertBossParameters,
    PcbStandoffParameters,
)


@dataclass(frozen=True)
class BoardFasteningArtifacts:
    """Derived parameters for one board-fastening backend."""

    standoff_parameters: tuple[
        PcbStandoffParameters,
        ...,
    ] = ()
    insert_boss_parameters: tuple[
        InsertBossParameters,
        ...,
    ] = ()
