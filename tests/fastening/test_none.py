"""Tests for the no-board-fastening backend."""

import cadquery as cq

from zcad.fastening import (
    BoardFasteningArtifacts,
    NoBoardFasteningBackend,
)


def test_none_backend_derives_empty_artifacts() -> None:
    backend = NoBoardFasteningBackend(
        strategy="none",
        fit_analyzer=lambda build, tolerance: (),
    )

    artifacts = backend.derive(
        assembly=object(),  # type: ignore[arg-type]
        specification=object(),  # type: ignore[arg-type]
        enclosure_parameters=object(),  # type: ignore[arg-type]
        policy=object(),
    )

    assert artifacts == BoardFasteningArtifacts()


def test_none_backend_preserves_body() -> None:
    backend = NoBoardFasteningBackend(
        strategy="none",
        fit_analyzer=lambda build, tolerance: (),
    )
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


def test_none_backend_delegates_fit_analysis() -> None:
    called = False

    def analyze(
        build: object,
        tolerance_mm: float,
    ) -> tuple[object, ...]:
        nonlocal called
        called = True

        assert build == "build"
        assert tolerance_mm == 0.01

        return ()

    backend = NoBoardFasteningBackend(
        strategy="none",
        fit_analyzer=analyze,  # type: ignore[arg-type]
    )

    assert (
        backend.analyze_fit(
            build="build",
            tolerance_mm=0.01,
        )
        == ()
    )
    assert called
