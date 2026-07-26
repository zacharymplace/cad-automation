"""Snap-retention board-fastening backend."""

from dataclasses import dataclass
from typing import cast

import cadquery as cq
from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureSpecification,
    InterferenceFinding,
)
from zcad_core.features import (
    SnapRetentionClipParameters,
    add_snap_retention_clip,
)

from zcad.fastening.artifacts import (
    BoardFasteningArtifacts,
)
from zcad.fastening.snap_retention import (
    SnapRetentionParameters,
    SnapRetentionPolicy,
    derive_snap_retention_parameters,
)
from zcad.fastening.verification import (
    BoardFasteningBuild,
    analyze_snap_retention_fit,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
)


def _core_clip_parameters(
    parameters: SnapRetentionParameters,
) -> SnapRetentionClipParameters:
    """Convert one automation artifact into core geometry parameters."""
    parameters.validate()

    return SnapRetentionClipParameters(
        x=parameters.x,
        y=parameters.y,
        base_height_mm=parameters.base_height_mm,
        compliant_span_mm=parameters.compliant_span_mm,
        board_thickness_mm=parameters.board_thickness_mm,
        width_mm=parameters.width_mm,
        wall_mm=parameters.wall_mm,
        height_mm=parameters.height_mm,
        overhang_mm=parameters.overhang_mm,
        clearance_mm=parameters.clearance_mm,
        base_z_mm=parameters.base_z_mm,
        rotation_degrees=parameters.rotation_degrees,
    )


def add_snap_retention_clips(
    *,
    body: cq.Workplane,
    parameters: tuple[
        SnapRetentionParameters,
        ...,
    ],
) -> cq.Workplane:
    """Add all derived snap-retention clips to an enclosure body."""
    result = body

    for clip in parameters:
        result = add_snap_retention_clip(
            result,
            parameters=_core_clip_parameters(clip),
        )

    return result


@dataclass(frozen=True)
class SnapRetentionBackend:
    """Backend for printed snap-retention clips."""

    strategy: object = "snap_retention"

    def derive(
        self,
        *,
        assembly: DeviceAssembly,
        specification: EnclosureSpecification,
        enclosure_parameters: EnclosureParameters,
        policy: object,
    ) -> BoardFasteningArtifacts:
        """Derive snap-retention artifacts."""
        return BoardFasteningArtifacts(
            snap_retention_parameters=(
                derive_snap_retention_parameters(
                    assembly=assembly,
                    specification=specification,
                    enclosure_parameters=enclosure_parameters,
                    policy=cast(
                        SnapRetentionPolicy,
                        policy,
                    ),
                )
            )
        )

    def apply(
        self,
        *,
        body: cq.Workplane,
        artifacts: BoardFasteningArtifacts,
    ) -> cq.Workplane:
        """Apply snap-retention geometry."""
        if artifacts.standoff_parameters:
            raise ValueError("snap-retention backend received standoff geometry")

        if artifacts.insert_boss_parameters:
            raise ValueError("snap-retention backend received insert-boss geometry")

        return add_snap_retention_clips(
            body=body,
            parameters=(artifacts.snap_retention_parameters),
        )

    def analyze_fit(
        self,
        *,
        build: BoardFasteningBuild,
        tolerance_mm: float,
    ) -> tuple[InterferenceFinding, ...]:
        """Verify generated snap-retention artifacts."""
        return analyze_snap_retention_fit(
            build,
            tolerance_mm=tolerance_mm,
        )
