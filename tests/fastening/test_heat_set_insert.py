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


def test_heat_set_backend_rejects_standoff_artifacts() -> None:
    backend = HeatSetInsertBackend()
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
