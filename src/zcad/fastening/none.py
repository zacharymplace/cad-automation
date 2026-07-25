"""Backend for enclosures without generated board mounts."""

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
from zcad.fastening.verification import (
    BoardFasteningBuild,
    analyze_no_board_fastening_fit,
)
from zcad.generators.enclosure import (
    EnclosureParameters,
)


@dataclass(frozen=True)
class NoBoardFasteningBackend:
    """Backend that intentionally generates no board mounts."""

    strategy: object = "none"

    def derive(
        self,
        *,
        assembly: DeviceAssembly,
        specification: EnclosureSpecification,
        enclosure_parameters: EnclosureParameters,
        policy: object,
    ) -> BoardFasteningArtifacts:
        """Return empty fastening artifacts."""
        del (
            assembly,
            specification,
            enclosure_parameters,
            policy,
        )

        return BoardFasteningArtifacts()

    def apply(
        self,
        *,
        body: cq.Workplane,
        artifacts: BoardFasteningArtifacts,
    ) -> cq.Workplane:
        """Return the body unchanged when no geometry is supplied."""
        if artifacts.standoff_parameters or artifacts.insert_boss_parameters:
            raise ValueError("none fastening backend received geometry")

        return body

    def analyze_fit(
        self,
        *,
        build: object,
        tolerance_mm: float,
    ) -> tuple[InterferenceFinding, ...]:
        """Verify the intentional absence of board mounts."""
        return analyze_no_board_fastening_fit(
            cast(BoardFasteningBuild, build),
            tolerance_mm=tolerance_mm,
        )
