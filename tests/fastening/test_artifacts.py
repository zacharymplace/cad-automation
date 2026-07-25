"""Tests for board-fastening artifacts."""

from zcad.fastening import (
    BoardFasteningArtifacts,
)


def test_board_fastening_artifacts_default_empty() -> None:
    artifacts = BoardFasteningArtifacts()

    assert artifacts.standoff_parameters == ()
    assert artifacts.insert_boss_parameters == ()
