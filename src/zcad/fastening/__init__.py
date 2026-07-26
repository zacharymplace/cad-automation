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
from zcad.fastening.snap_retention import (
    SnapRetentionParameters,
    SnapRetentionPolicy,
)
from zcad.fastening.verification import (
    BoardFasteningBuild,
    BoardFasteningVerificationPolicy,
    analyze_heat_set_insert_fit,
    analyze_mount_positions,
    analyze_no_board_fastening_fit,
    analyze_printed_standoff_fit,
    expected_board_mounting_positions,
    mounting_finding,
)

__all__ = (
    "SnapRetentionPolicy",
    "SnapRetentionParameters",
    "BoardFasteningBuild",
    "BoardFasteningVerificationPolicy",
    "analyze_heat_set_insert_fit",
    "analyze_no_board_fastening_fit",
    "analyze_printed_standoff_fit",
    "analyze_mount_positions",
    "expected_board_mounting_positions",
    "mounting_finding",
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
