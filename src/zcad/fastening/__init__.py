"""Reusable board-fastening generation and verification."""

from zcad.fastening.artifacts import (
    BoardFasteningArtifacts,
)
from zcad.fastening.backend import (
    BoardFasteningBackend,
)
from zcad.fastening.heat_set_insert import (
    HeatSetInsertBackend,
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
    "NoBoardFasteningBackend",
    "PrintedStandoffBackend",
    "PrintedStandoffPolicy",
    "add_board_standoffs",
    "derive_board_standoff_parameters",
)
