"""Board-fastening backend contracts."""

from typing import Protocol

import cadquery as cq
from zcad_core.assemblies import (
    DeviceAssembly,
    EnclosureSpecification,
    InterferenceFinding,
)

from zcad.fastening.artifacts import (
    BoardFasteningArtifacts,
)
from zcad.fastening.verification import (
    BoardFasteningBuild,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
)


class BoardFasteningBackend(Protocol):
    """Generation and verification interface for one fastening strategy."""

    strategy: object

    def derive(
        self,
        *,
        assembly: DeviceAssembly,
        specification: EnclosureSpecification,
        enclosure_parameters: EnclosureParameters,
        policy: object,
    ) -> BoardFasteningArtifacts:
        """Derive strategy-specific fastening parameters."""
        ...

    def apply(
        self,
        *,
        body: cq.Workplane,
        artifacts: BoardFasteningArtifacts,
    ) -> cq.Workplane:
        """Apply strategy-specific fastening geometry."""
        ...

    def analyze_fit(
        self,
        *,
        build: BoardFasteningBuild,
        tolerance_mm: float,
    ) -> tuple[InterferenceFinding, ...]:
        """Verify strategy-specific fastening geometry."""
        ...
