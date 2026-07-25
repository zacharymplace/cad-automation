"""Tests for board-fastening verification contracts."""

from dataclasses import dataclass

from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureSpecification,
)

from zcad.fastening import (
    BoardFasteningBuild,
    BoardFasteningVerificationPolicy,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
)


@dataclass(frozen=True)
class ExamplePolicy:
    """Minimal policy satisfying the verification contract."""

    standoff_radial_wall_mm: float = 1.5
    standoff_hole_clearance_mm: float | None = None
    board_fastener: str | None = "m2"
    insert_boss_radial_wall_mm: float = 1.8


@dataclass(frozen=True)
class ExampleBuild:
    """Minimal build satisfying the verification contract."""

    assembly: DeviceAssembly
    specification: EnclosureSpecification
    enclosure_parameters: EnclosureParameters
    policy: ExamplePolicy
    standoff_parameters: tuple = ()
    insert_boss_parameters: tuple = ()


def test_verification_policy_is_structural() -> None:
    policy = ExamplePolicy()

    assert isinstance(
        policy,
        BoardFasteningVerificationPolicy,
    )


def test_verification_build_is_structural() -> None:
    build = ExampleBuild(
        assembly=DeviceAssembly(),
        specification=EnclosureSpecification(
            inner_width_mm=10.0,
            inner_depth_mm=10.0,
            inner_height_mm=10.0,
            center_x_mm=0.0,
            center_y_mm=0.0,
            bottom_z_mm=0.0,
            connector_identifier="test_connector",
            cable_edge="positive_x",
            cable_width_mm=2.0,
            cable_height_mm=2.0,
            cable_center_offset_mm=0.0,
            cable_bottom_z_mm=1.0,
        ),
        enclosure_parameters=EnclosureParameters(
            width=16.0,
            depth=16.0,
            height=13.0,
            wall=3.0,
            floor=3.0,
        ),
        policy=ExamplePolicy(),
    )

    assert isinstance(
        build,
        BoardFasteningBuild,
    )
