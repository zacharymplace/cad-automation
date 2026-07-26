"""Tests for snap-retention metadata derivation."""

from dataclasses import dataclass

import cadquery as cq
import pytest
from zcad_core.assemblies import (
    AssemblyComponent,
    DeviceAssembly,
    EnclosureSpecification,
    Placement,
)
from zcad_core.features import (
    InsertBossParameters,
    PcbStandoffParameters,
)

from zcad.fastening import (
    BoardFasteningArtifacts,
    SnapRetentionBackend,
    SnapRetentionPolicy,
    derive_snap_retention_parameters,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
)


@dataclass(frozen=True)
class ExamplePolicy:
    """Concrete policy used by snap derivation tests."""

    snap_clip_wall_mm: float = 1.2
    snap_clip_height_mm: float = 4.0
    snap_clip_overhang_mm: float = 0.6
    snap_clip_clearance_mm: float = 0.25


def _specification() -> EnclosureSpecification:
    return EnclosureSpecification(
        inner_width_mm=40.0,
        inner_depth_mm=60.0,
        inner_height_mm=15.0,
        center_x_mm=2.0,
        center_y_mm=-3.0,
        bottom_z_mm=-5.0,
        connector_identifier="connector",
        cable_edge="negative_y",
        cable_width_mm=10.0,
        cable_height_mm=5.0,
        cable_center_offset_mm=0.0,
        cable_bottom_z_mm=-2.0,
    )


def _enclosure_parameters() -> EnclosureParameters:
    return EnclosureParameters(
        width=46.0,
        depth=66.0,
        height=18.0,
        wall=3.0,
        floor=3.0,
    )


def _assembly(
    *,
    metadata: object | None = None,
    placement: Placement | None = None,
) -> DeviceAssembly:
    resolved_metadata = {} if metadata is None else {"retention": metadata}

    board = AssemblyComponent(
        identifier="board",
        geometry=(
            cq.Workplane("XY").box(
                20.0,
                40.0,
                1.6,
                centered=(True, True, False),
            )
        ),
        placement=(placement if placement is not None else Placement()),
        metadata=resolved_metadata,
    )

    return DeviceAssembly((board,))


def _retention_metadata() -> dict[str, object]:
    return {
        "board_thickness_mm": 1.6,
        "insertion_axis": "positive_z",
        "clip_regions": (
            {
                "edge": "negative_x",
                "center_offset_mm": 3.0,
                "width_mm": 6.0,
                "edge_clearance_mm": 0.5,
            },
            {
                "edge": "positive_y",
                "center_offset_mm": -4.0,
                "width_mm": 5.0,
                "edge_clearance_mm": 0.25,
            },
        ),
        "keepout_regions": (),
    }


def test_policy_is_structural() -> None:
    assert isinstance(
        ExamplePolicy(),
        SnapRetentionPolicy,
    )


def test_missing_retention_metadata_returns_empty_tuple() -> None:
    parameters = derive_snap_retention_parameters(
        assembly=_assembly(),
        specification=_specification(),
        enclosure_parameters=_enclosure_parameters(),
        policy=ExamplePolicy(),
    )

    assert parameters == ()


def test_retention_metadata_must_be_dictionary() -> None:
    with pytest.raises(
        TypeError,
        match="must be a dictionary",
    ):
        derive_snap_retention_parameters(
            assembly=_assembly(
                metadata=("not", "a", "dictionary"),
            ),
            specification=_specification(),
            enclosure_parameters=(_enclosure_parameters()),
            policy=ExamplePolicy(),
        )


def test_multiple_clip_regions_derive_parameters() -> None:
    parameters = derive_snap_retention_parameters(
        assembly=_assembly(
            metadata=_retention_metadata(),
        ),
        specification=_specification(),
        enclosure_parameters=_enclosure_parameters(),
        policy=ExamplePolicy(),
    )

    assert len(parameters) == 2

    negative_x, positive_y = parameters

    assert negative_x.x == pytest.approx(-12.5)
    assert negative_x.y == pytest.approx(6.0)
    assert negative_x.width_mm == 6.0
    assert negative_x.rotation_degrees == 180.0

    assert positive_y.x == pytest.approx(-6.0)
    assert positive_y.y == pytest.approx(23.25)
    assert positive_y.width_mm == 5.0
    assert positive_y.rotation_degrees == 90.0


def test_policy_values_propagate_to_parameters() -> None:
    policy = ExamplePolicy(
        snap_clip_wall_mm=1.4,
        snap_clip_height_mm=4.5,
        snap_clip_overhang_mm=0.7,
        snap_clip_clearance_mm=0.3,
    )

    parameters = derive_snap_retention_parameters(
        assembly=_assembly(
            metadata=_retention_metadata(),
        ),
        specification=_specification(),
        enclosure_parameters=_enclosure_parameters(),
        policy=policy,
    )

    first = parameters[0]

    assert first.wall_mm == 1.4
    assert first.height_mm == 4.5
    assert first.overhang_mm == 0.7
    assert first.clearance_mm == 0.3
    assert first.compliant_span_mm == pytest.approx(6.0 + 1.6 + 0.3)
    assert first.base_z_mm == -9.0
    assert first.base_height_mm == pytest.approx(3.0)
    assert first.support_height_mm == pytest.approx(6.0)
    assert first.board_thickness_mm == pytest.approx(1.6)


def test_z_rotation_transforms_position_and_orientation() -> None:
    metadata = {
        **_retention_metadata(),
        "clip_regions": (
            {
                "edge": "positive_x",
                "center_offset_mm": 0.0,
                "width_mm": 6.0,
                "edge_clearance_mm": 0.5,
            },
        ),
    }

    parameters = derive_snap_retention_parameters(
        assembly=_assembly(
            metadata=metadata,
            placement=Placement(
                x_mm=10.0,
                y_mm=5.0,
                rotation_z_deg=90.0,
            ),
        ),
        specification=_specification(),
        enclosure_parameters=_enclosure_parameters(),
        policy=ExamplePolicy(),
    )

    clip = parameters[0]

    assert clip.x == pytest.approx(8.0)
    assert clip.y == pytest.approx(18.5)
    assert clip.rotation_degrees == 90.0


@pytest.mark.parametrize(
    "placement",
    [
        Placement(rotation_x_deg=10.0),
        Placement(rotation_y_deg=10.0),
    ],
)
def test_x_and_y_rotations_are_rejected(
    placement: Placement,
) -> None:
    with pytest.raises(
        ValueError,
        match="does not support board X or Y rotation",
    ):
        derive_snap_retention_parameters(
            assembly=_assembly(
                metadata=_retention_metadata(),
                placement=placement,
            ),
            specification=_specification(),
            enclosure_parameters=(_enclosure_parameters()),
            policy=ExamplePolicy(),
        )


def test_negative_z_insertion_is_not_yet_supported() -> None:
    metadata = {
        **_retention_metadata(),
        "insertion_axis": "negative_z",
    }

    with pytest.raises(
        ValueError,
        match="only positive_z insertion",
    ):
        derive_snap_retention_parameters(
            assembly=_assembly(metadata=metadata),
            specification=_specification(),
            enclosure_parameters=(_enclosure_parameters()),
            policy=ExamplePolicy(),
        )


def test_backend_derives_snap_artifacts() -> None:
    artifacts = SnapRetentionBackend().derive(
        assembly=_assembly(
            metadata=_retention_metadata(),
        ),
        specification=_specification(),
        enclosure_parameters=_enclosure_parameters(),
        policy=ExamplePolicy(),
    )

    assert len(artifacts.snap_retention_parameters) == 2
    assert artifacts.standoff_parameters == ()
    assert artifacts.insert_boss_parameters == ()


def test_backend_applies_snap_retention_geometry() -> None:
    body = (
        cq.Workplane("XY")
        .box(
            46.0,
            66.0,
            3.0,
            centered=(True, True, False),
        )
        .translate(
            (
                0.0,
                0.0,
                -9.0,
            )
        )
    )

    artifacts = SnapRetentionBackend().derive(
        assembly=_assembly(
            metadata=_retention_metadata(),
        ),
        specification=_specification(),
        enclosure_parameters=_enclosure_parameters(),
        policy=ExamplePolicy(),
    )

    result = SnapRetentionBackend().apply(
        body=body,
        artifacts=artifacts,
    )

    assert result.val().isValid()
    assert result.val().Volume() > body.val().Volume()


def test_backend_with_no_snap_artifacts_preserves_body() -> None:
    body = cq.Workplane("XY").box(
        20.0,
        20.0,
        3.0,
        centered=(True, True, False),
    )

    result = SnapRetentionBackend().apply(
        body=body,
        artifacts=BoardFasteningArtifacts(),
    )

    assert result.val().isValid()
    assert result.val().Volume() == pytest.approx(body.val().Volume())


def test_backend_rejects_standoff_artifacts() -> None:
    with pytest.raises(
        ValueError,
        match="received standoff geometry",
    ):
        SnapRetentionBackend().apply(
            body=cq.Workplane("XY").box(
                20.0,
                20.0,
                3.0,
            ),
            artifacts=BoardFasteningArtifacts(
                standoff_parameters=(
                    PcbStandoffParameters(
                        x=0.0,
                        y=0.0,
                        base_height_mm=3.0,
                        standoff_height_mm=4.0,
                        outer_diameter_mm=5.0,
                        hole_diameter_mm=2.0,
                    ),
                ),
            ),
        )


def test_backend_rejects_insert_boss_artifacts() -> None:
    with pytest.raises(
        ValueError,
        match="received insert-boss geometry",
    ):
        SnapRetentionBackend().apply(
            body=cq.Workplane("XY").box(
                20.0,
                20.0,
                3.0,
            ),
            artifacts=BoardFasteningArtifacts(
                insert_boss_parameters=(
                    InsertBossParameters(
                        x=0.0,
                        y=0.0,
                        base_height_mm=3.0,
                        boss_height_mm=5.0,
                        boss_outer_diameter_mm=6.0,
                        pilot_hole_diameter_mm=2.0,
                        insert_pocket_diameter_mm=3.0,
                        insert_pocket_depth_mm=3.0,
                    ),
                ),
            ),
        )
