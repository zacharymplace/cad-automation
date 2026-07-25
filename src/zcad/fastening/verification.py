"""Reusable board-fastening verification contracts."""

from math import hypot
from typing import Protocol, runtime_checkable

from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureSpecification,
    InterferenceFinding,
    assembly_mounting_hole_positions,
)
from zcad_core.features import (
    InsertBossParameters,
    PcbStandoffParameters,
)
from zcad_core.hardware import get_fastener

from zcad.generators.enclosure import (
    EnclosureParameters,
)


@runtime_checkable
class BoardFasteningVerificationPolicy(Protocol):
    """Policy fields required for fastening verification."""

    standoff_radial_wall_mm: float
    standoff_hole_clearance_mm: float | None

    board_fastener: str | None
    insert_boss_radial_wall_mm: float


@runtime_checkable
class BoardFasteningBuild(Protocol):
    """Build data required to verify board fastening."""

    assembly: DeviceAssembly
    specification: EnclosureSpecification
    enclosure_parameters: EnclosureParameters
    policy: BoardFasteningVerificationPolicy

    standoff_parameters: tuple[
        PcbStandoffParameters,
        ...,
    ]
    insert_boss_parameters: tuple[
        InsertBossParameters,
        ...,
    ]


def mounting_finding(
    *,
    identifier: str,
    kind: str,
    required: float,
    measured: float,
) -> InterferenceFinding:
    """Create one assembly-mounting verification finding."""
    return InterferenceFinding(
        first_identifier="board",
        second_identifier=identifier,
        kind=kind,
        required_clearance_mm=required,
        measured_clearance_mm=measured,
        clearance_source="assembly_mounting",
    )


def expected_board_mounting_positions(
    build: BoardFasteningBuild,
) -> tuple[tuple[float, float, float], ...]:
    """Return expected enclosure-local board mounting positions."""
    board = build.assembly.get("board")
    world_positions = assembly_mounting_hole_positions(board)

    return tuple(
        (
            world_x_mm - build.specification.center_x_mm,
            world_y_mm - build.specification.center_y_mm,
            world_z_mm,
        )
        for (
            world_x_mm,
            world_y_mm,
            world_z_mm,
        ) in world_positions
    )


def analyze_mount_positions(
    *,
    build: BoardFasteningBuild,
    actual: tuple[object, ...],
    identifier_prefix: str,
    height_attribute: str,
    tolerance_mm: float,
) -> list[InterferenceFinding]:
    """Verify count, XY position, and mounting height."""
    expected_positions = expected_board_mounting_positions(build)

    if not expected_positions:
        return []

    findings: list[InterferenceFinding] = []

    if len(actual) != len(expected_positions):
        findings.append(
            mounting_finding(
                identifier="board_mounts",
                kind="mounting_count",
                required=float(len(expected_positions)),
                measured=float(len(actual)),
            )
        )

    for index, (
        parameters,
        expected,
    ) in enumerate(
        zip(
            actual,
            expected_positions,
            strict=False,
        ),
        start=1,
    ):
        expected_x_mm, expected_y_mm, board_bottom_z_mm = expected
        identifier = f"{identifier_prefix}_{index}"

        parameter_x_mm = parameters.x
        parameter_y_mm = parameters.y

        center_offset_mm = hypot(
            parameter_x_mm - expected_x_mm,
            parameter_y_mm - expected_y_mm,
        )

        if center_offset_mm > tolerance_mm:
            findings.append(
                mounting_finding(
                    identifier=identifier,
                    kind="mounting_alignment",
                    required=tolerance_mm,
                    measured=center_offset_mm,
                )
            )

        expected_height_mm = board_bottom_z_mm - build.specification.bottom_z_mm
        measured_height_mm = getattr(
            parameters,
            height_attribute,
        )
        height_error_mm = abs(measured_height_mm - expected_height_mm)

        if height_error_mm > tolerance_mm:
            findings.append(
                mounting_finding(
                    identifier=identifier,
                    kind="mounting_height",
                    required=tolerance_mm,
                    measured=height_error_mm,
                )
            )

    return findings


def analyze_no_board_fastening_fit(
    build: BoardFasteningBuild,
    *,
    tolerance_mm: float,
) -> tuple[InterferenceFinding, ...]:
    """Verify the intentional absence of board mounts."""
    del tolerance_mm

    expected_positions = expected_board_mounting_positions(build)

    if not expected_positions:
        return ()

    return (
        mounting_finding(
            identifier="board_mounts",
            kind="mounting_count",
            required=float(len(expected_positions)),
            measured=0.0,
        ),
    )


def analyze_printed_standoff_fit(
    build: BoardFasteningBuild,
    *,
    tolerance_mm: float,
) -> tuple[InterferenceFinding, ...]:
    """Verify printed standoffs against assembly metadata."""
    board = build.assembly.get("board")
    expected_positions = expected_board_mounting_positions(build)

    if not expected_positions:
        return ()

    findings = analyze_mount_positions(
        build=build,
        actual=build.standoff_parameters,
        identifier_prefix="standoff",
        height_attribute="standoff_height_mm",
        tolerance_mm=tolerance_mm,
    )

    mounting = board.metadata.get("mounting")

    if not isinstance(mounting, dict):
        raise TypeError("board mounting metadata must be a dictionary")

    hole_diameter_mm = mounting.get("hole_diameter_mm")
    recommended_clearance_mm = mounting.get("recommended_clearance_mm")

    if not isinstance(
        hole_diameter_mm,
        int | float,
    ):
        raise TypeError("board mounting hole diameter must be numeric")

    if not isinstance(
        recommended_clearance_mm,
        int | float,
    ):
        raise TypeError("board mounting clearance must be numeric")

    resolved_clearance_mm = (
        build.policy.standoff_hole_clearance_mm
        if build.policy.standoff_hole_clearance_mm is not None
        else recommended_clearance_mm
    )

    expected_hole_diameter_mm = hole_diameter_mm + resolved_clearance_mm
    expected_outer_diameter_mm = (
        expected_hole_diameter_mm + 2 * build.policy.standoff_radial_wall_mm
    )

    for index, parameters in enumerate(
        build.standoff_parameters,
        start=1,
    ):
        identifier = f"standoff_{index}"

        if abs(parameters.hole_diameter_mm - expected_hole_diameter_mm) > tolerance_mm:
            findings.append(
                mounting_finding(
                    identifier=identifier,
                    kind=("mounting_hole_diameter"),
                    required=(expected_hole_diameter_mm),
                    measured=(parameters.hole_diameter_mm),
                )
            )

        if (
            abs(parameters.outer_diameter_mm - expected_outer_diameter_mm)
            > tolerance_mm
        ):
            findings.append(
                mounting_finding(
                    identifier=identifier,
                    kind=("mounting_boss_diameter"),
                    required=(expected_outer_diameter_mm),
                    measured=(parameters.outer_diameter_mm),
                )
            )

    return tuple(findings)


def analyze_heat_set_insert_fit(
    build: BoardFasteningBuild,
    *,
    tolerance_mm: float,
) -> tuple[InterferenceFinding, ...]:
    """Verify insert bosses against fastener policy."""
    expected_positions = expected_board_mounting_positions(build)

    if not expected_positions:
        return ()

    findings = analyze_mount_positions(
        build=build,
        actual=build.insert_boss_parameters,
        identifier_prefix="insert_boss",
        height_attribute="boss_height_mm",
        tolerance_mm=tolerance_mm,
    )

    if build.policy.board_fastener is None:
        raise ValueError("board_fastener is required for heat-set insert fastening")

    fastener = get_fastener(build.policy.board_fastener)
    insert_diameter_mm = fastener.heat_set_insert_diameter_mm
    insert_depth_mm = fastener.heat_set_insert_depth_mm

    if insert_diameter_mm is None or insert_depth_mm is None:
        raise ValueError("fastener does not define heat-set insert dimensions")

    expected_outer_diameter_mm = (
        insert_diameter_mm + 2 * build.policy.insert_boss_radial_wall_mm
    )

    for index, parameters in enumerate(
        build.insert_boss_parameters,
        start=1,
    ):
        identifier = f"insert_boss_{index}"

        checks = (
            (
                "mounting_pilot_hole_diameter",
                fastener.tap_hole_mm,
                parameters.pilot_hole_diameter_mm,
            ),
            (
                "mounting_insert_pocket_diameter",
                insert_diameter_mm,
                parameters.insert_pocket_diameter_mm,
            ),
            (
                "mounting_insert_pocket_depth",
                insert_depth_mm,
                parameters.insert_pocket_depth_mm,
            ),
            (
                "mounting_boss_diameter",
                expected_outer_diameter_mm,
                parameters.boss_outer_diameter_mm,
            ),
        )

        for kind, required, measured in checks:
            if abs(measured - required) > tolerance_mm:
                findings.append(
                    mounting_finding(
                        identifier=identifier,
                        kind=kind,
                        required=required,
                        measured=measured,
                    )
                )

    return tuple(findings)
