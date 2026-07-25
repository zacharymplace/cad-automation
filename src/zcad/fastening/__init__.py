"""Reusable board-fastening generation and verification."""

from zcad.fastening.artifacts import (
    BoardFasteningArtifacts,
)
from zcad.fastening.backend import (
    BoardFasteningBackend,
)
from zcad.fastening.heat_set_insert import (
    HeatSetInsertBackend,
    HeatSetInsertPolicy,
    add_board_insert_bosses,
    derive_board_insert_boss_parameters,
)
from zcad.fastening.none import (
    NoBoardFasteningBackend,
)
from zcad.fastening.printed_standoff import (
    PrintedStandoffBackend,
    PrintedStandoffPolicy,
    add_board_standoffs,
    derive_board_standoff_parameters,
)

__all__ = (
    "BoardFasteningArtifacts",
    "BoardFasteningBackend",
    "HeatSetInsertBackend",
    "HeatSetInsertPolicy",
    "NoBoardFasteningBackend",
    "PrintedStandoffBackend",
    "PrintedStandoffPolicy",
    "add_board_insert_bosses",
    "add_board_standoffs",
    "derive_board_insert_boss_parameters",
    "derive_board_standoff_parameters",
)
