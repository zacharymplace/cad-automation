"""Heat-set insert boss calibration coupon."""

from dataclasses import dataclass

import cadquery as cq
from zcad_core.features import (
    InsertBossParameters,
    add_heat_set_insert_boss,
)
from zcad_core.features.labels import (
    add_embossed_label,
)
from zcad_core.hardware import (
    get_fastener,
)


@dataclass(frozen=True)
class InsertBossCouponParameters:
    """Parameters for an insert-boss calibration coupon."""

    width_mm: float = 120.0
    depth_mm: float = 30.0
    base_height_mm: float = 3.0
    label_size_mm: float = 5.0
    emboss_height_mm: float = 0.6


def build_insert_boss_coupon(
    parameters: InsertBossCouponParameters,
) -> cq.Workplane:
    """Build a four-fastener insert boss calibration coupon."""
    model = cq.Workplane("XY").box(
        parameters.width_mm,
        parameters.depth_mm,
        parameters.base_height_mm,
    )

    positions = [
        (-45.0, "M2"),
        (-15.0, "M2.5"),
        (15.0, "M3"),
        (45.0, "M4"),
    ]

    for x, identifier in positions:
        model = add_heat_set_insert_boss(
            model,
            parameters=InsertBossParameters.from_fastener(
                fastener=get_fastener(identifier),
                x=x,
                y=0.0,
                base_height_mm=parameters.base_height_mm,
            ),
        )

        model = add_embossed_label(
            model,
            text=identifier,
            x=x,
            y=-10.0,
            base_height=parameters.base_height_mm,
            text_size=parameters.label_size_mm,
            emboss_height=parameters.emboss_height_mm,
        )

    return model
