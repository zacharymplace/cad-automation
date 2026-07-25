"""Tests for the no-board-fastening backend."""

import cadquery as cq

from zcad.fastening import (
    BoardFasteningArtifacts,
    NoBoardFasteningBackend,
)


def test_none_backend_derives_empty_artifacts() -> None:
    backend = NoBoardFasteningBackend(strategy="none")

    artifacts = backend.derive(
        assembly=object(),  # type: ignore[arg-type]
        specification=object(),  # type: ignore[arg-type]
        enclosure_parameters=object(),  # type: ignore[arg-type]
        policy=object(),
    )

    assert artifacts == BoardFasteningArtifacts()


def test_none_backend_preserves_body() -> None:
    backend = NoBoardFasteningBackend(strategy="none")
    body = cq.Workplane("XY").box(
        10.0,
        10.0,
        3.0,
    )

    result = backend.apply(
        body=body,
        artifacts=BoardFasteningArtifacts(),
    )

    assert result.val().Volume() == body.val().Volume()
