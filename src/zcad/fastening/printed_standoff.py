"""Printed-standoff fastening backend."""

from collections.abc import Callable
from dataclasses import dataclass

import cadquery as cq
from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureSpecification,
    InterferenceFinding,
)

from zcad.fastening.artifacts import (
    BoardFasteningArtifacts,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
)

DeriveCallback = Callable[..., BoardFasteningArtifacts]
ApplyCallback = Callable[
    [cq.Workplane, BoardFasteningArtifacts],
    cq.Workplane,
]
FitCallback = Callable[
    [object, float],
    tuple[InterferenceFinding, ...],
]


@dataclass(frozen=True)
class PrintedStandoffBackend:
    """Backend for printed PCB standoffs."""

    strategy: object = "printed_standoff"
    derive_callback: DeriveCallback | None = None
    apply_callback: ApplyCallback | None = None
    fit_callback: FitCallback | None = None

    def derive(
        self,
        *,
        assembly: DeviceAssembly,
        specification: EnclosureSpecification,
        enclosure_parameters: EnclosureParameters,
        policy: object,
    ) -> BoardFasteningArtifacts:
        """Derive printed-standoff artifacts."""
        if self.derive_callback is None:
            raise RuntimeError("printed standoff derive callback is not configured")

        return self.derive_callback(
            assembly=assembly,
            specification=specification,
            enclosure_parameters=enclosure_parameters,
            policy=policy,
        )

    def apply(
        self,
        *,
        body: cq.Workplane,
        artifacts: BoardFasteningArtifacts,
    ) -> cq.Workplane:
        """Apply printed-standoff geometry."""
        if artifacts.insert_boss_parameters:
            raise ValueError("printed standoff backend received insert-boss geometry")

        if self.apply_callback is None:
            raise RuntimeError("printed standoff apply callback is not configured")

        return self.apply_callback(
            body,
            artifacts,
        )

    def analyze_fit(
        self,
        *,
        build: object,
        tolerance_mm: float,
    ) -> tuple[InterferenceFinding, ...]:
        """Verify printed-standoff geometry."""
        if self.fit_callback is None:
            raise RuntimeError("printed standoff fit callback is not configured")

        return self.fit_callback(
            build,
            tolerance_mm,
        )
