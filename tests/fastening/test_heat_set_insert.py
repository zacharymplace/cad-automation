"""Tests for the heat-set insert fastening backend."""

import cadquery as cq
import pytest
from zcad_core.features import (
    PcbStandoffParameters,
)

from zcad.fastening import (
    BoardFasteningArtifacts,
    HeatSetInsertBackend,
)


def test_heat_set_backend_delegates_derivation() -> None:
    called = False

    def derive(**kwargs: object) -> BoardFasteningArtifacts:
        nonlocal called
        called = True

        assert set(kwargs) == {
            "assembly",
            "specification",
            "enclosure_parameters",
            "policy",
        }

        return BoardFasteningArtifacts()

    backend = HeatSetInsertBackend(
        derive_callback=derive,
    )

    assert (
        backend.derive(
            assembly=object(),  # type: ignore[arg-type]
            specification=object(),  # type: ignore[arg-type]
            enclosure_parameters=object(),  # type: ignore[arg-type]
            policy=object(),
        )
        == BoardFasteningArtifacts()
    )
    assert called


def test_heat_set_backend_rejects_standoff_artifacts() -> None:
    backend = HeatSetInsertBackend(
        apply_callback=lambda body, artifacts: body,
    )
    artifacts = BoardFasteningArtifacts(
        standoff_parameters=(
            PcbStandoffParameters(
                x=0.0,
                y=0.0,
                base_height_mm=3.0,
                standoff_height_mm=3.0,
                outer_diameter_mm=5.6,
                hole_diameter_mm=2.6,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="standoff geometry",
    ):
        backend.apply(
            body=cq.Workplane("XY").box(
                10.0,
                10.0,
                3.0,
            ),
            artifacts=artifacts,
        )


def test_heat_set_backend_delegates_fit_analysis() -> None:
    called = False

    def analyze(
        build: object,
        tolerance_mm: float,
    ) -> tuple[object, ...]:
        nonlocal called
        called = True

        assert build == "build"
        assert tolerance_mm == pytest.approx(0.01)

        return ()

    backend = HeatSetInsertBackend(
        fit_callback=analyze,  # type: ignore[arg-type]
    )

    assert (
        backend.analyze_fit(
            build="build",
            tolerance_mm=0.01,
        )
        == ()
    )
    assert called
