"""Snap-retention board-fastening backend."""

from dataclasses import dataclass
from typing import cast

import cadquery as cq
from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureSpecification,
    InterferenceFinding,
)

from zcad.fastening.artifacts import (
    BoardFasteningArtifacts,
)
from zcad.fastening.snap_retention import (
    SnapRetentionPolicy,
    derive_snap_retention_parameters,
)
from zcad.fastening.verification import (
    BoardFasteningBuild,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
)


@dataclass(frozen=True)
class SnapRetentionBackend:
    """Backend shell for printed snap-retention clips."""

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
                    enclosure_parameters=(enclosure_parameters),
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
        del body
        del artifacts

        raise NotImplementedError("snap-retention geometry not implemented")

    def analyze_fit(
        self,
        *,
        build: BoardFasteningBuild,
        tolerance_mm: float,
    ) -> tuple[InterferenceFinding, ...]:
        """Return no findings until verification is implemented."""
        del build
        del tolerance_mm

        return ()
