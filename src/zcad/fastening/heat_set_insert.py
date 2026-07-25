"""Heat-set insert board-fastening backend."""

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
class HeatSetInsertBackend:
    """Backend for heat-set insert PCB bosses."""

    strategy: object = "heat_set_insert"
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
        """Derive heat-set insert artifacts."""
        if self.derive_callback is None:
            raise RuntimeError("heat-set insert derive callback is not configured")

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
        """Apply heat-set insert boss geometry."""
        if artifacts.standoff_parameters:
            raise ValueError("heat-set insert backend received standoff geometry")

        if self.apply_callback is None:
            raise RuntimeError("heat-set insert apply callback is not configured")

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
        """Verify heat-set insert boss geometry."""
        if self.fit_callback is None:
            raise RuntimeError("heat-set insert fit callback is not configured")

        return self.fit_callback(
            build,
            tolerance_mm,
        )
