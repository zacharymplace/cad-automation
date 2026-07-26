"""Tests for snap-retention fastening artifacts."""

import pytest

from zcad.fastening import (
    BoardFasteningArtifacts,
    SnapRetentionParameters,
)


def test_snap_retention_parameters_validate() -> None:
    parameters = SnapRetentionParameters(
        x=0.0,
        y=0.0,
        base_height_mm=3.0,
        support_height_mm=4.0,
        board_thickness_mm=1.6,
        width_mm=6.0,
        wall_mm=1.2,
        height_mm=4.0,
        overhang_mm=0.6,
        clearance_mm=0.25,
        flex_length_mm=8.0,
        base_z_mm=-5.0,
    )

    parameters.validate()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("base_height_mm", 0.0),
        ("support_height_mm", 0.0),
        ("board_thickness_mm", 0.0),
        ("width_mm", 0.0),
        ("wall_mm", 0.0),
        ("height_mm", 0.0),
        ("overhang_mm", 0.0),
        ("flex_length_mm", 0.0),
    ],
)
def test_snap_retention_rejects_nonpositive_dimensions(
    field: str,
    value: float,
) -> None:
    values = {
        "x": 0.0,
        "y": 0.0,
        "base_height_mm": 3.0,
        "support_height_mm": 4.0,
        "board_thickness_mm": 1.6,
        "width_mm": 6.0,
        "wall_mm": 1.2,
        "height_mm": 4.0,
        "overhang_mm": 0.6,
        "clearance_mm": 0.25,
        "flex_length_mm": 8.0,
        "base_z_mm": -5.0,
    }
    values[field] = value

    parameters = SnapRetentionParameters(
        **values,
    )

    with pytest.raises(
        ValueError,
        match=f"{field} must be greater than zero",
    ):
        parameters.validate()


def test_snap_retention_rejects_negative_clearance() -> None:
    parameters = SnapRetentionParameters(
        x=0.0,
        y=0.0,
        base_height_mm=3.0,
        support_height_mm=4.0,
        board_thickness_mm=1.6,
        width_mm=6.0,
        wall_mm=1.2,
        height_mm=4.0,
        overhang_mm=0.6,
        clearance_mm=-0.01,
        flex_length_mm=8.0,
        base_z_mm=-5.0,
    )

    with pytest.raises(
        ValueError,
        match="clearance_mm must not be negative",
    ):
        parameters.validate()


def test_artifacts_preserve_snap_retention_parameters() -> None:
    parameters = SnapRetentionParameters(
        x=1.0,
        y=2.0,
        base_height_mm=3.0,
        support_height_mm=4.0,
        board_thickness_mm=1.6,
        width_mm=6.0,
        wall_mm=1.2,
        height_mm=4.0,
        overhang_mm=0.6,
        clearance_mm=0.25,
        flex_length_mm=8.0,
        base_z_mm=-5.0,
        rotation_degrees=90.0,
    )

    artifacts = BoardFasteningArtifacts(
        snap_retention_parameters=(parameters,),
    )

    assert artifacts.snap_retention_parameters == (parameters,)
