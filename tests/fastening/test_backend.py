"""Tests for the board-fastening backend contract."""

from typing import get_type_hints

from zcad.fastening import (
    BoardFasteningBackend,
)


def test_backend_protocol_exposes_required_operations() -> None:
    assert hasattr(
        BoardFasteningBackend,
        "derive",
    )
    assert hasattr(
        BoardFasteningBackend,
        "apply",
    )
    assert hasattr(
        BoardFasteningBackend,
        "analyze_fit",
    )


def test_backend_protocol_declares_strategy() -> None:
    hints = get_type_hints(BoardFasteningBackend)

    assert "strategy" in hints
