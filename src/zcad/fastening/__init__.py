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
    derive_snap_retention_parameters,
)
from zcad.fastening.snap_retention_backend import (
    SnapRetentionBackend,
    add_snap_retention_clips,
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
    "BoardFasteningArtifacts",
    "BoardFasteningBackend",
    "BoardFasteningBuild",
    "BoardFasteningVerificationPolicy",
    "HeatSetInsertBackend",
    "HeatSetInsertPolicy",
    "NoBoardFasteningBackend",
    "PrintedStandoffBackend",
    "PrintedStandoffPolicy",
    "SnapRetentionBackend",
    "SnapRetentionParameters",
    "SnapRetentionPolicy",
    "add_board_insert_bosses",
    "add_board_standoffs",
    "add_snap_retention_clips",
    "analyze_heat_set_insert_fit",
    "analyze_mount_positions",
    "analyze_no_board_fastening_fit",
    "analyze_printed_standoff_fit",
    "derive_board_insert_boss_parameters",
    "derive_board_standoff_parameters",
    "derive_snap_retention_parameters",
    "expected_board_mounting_positions",
    "mounting_finding",
)
