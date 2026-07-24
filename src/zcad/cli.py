"""Generate CAD models from JSON specifications."""

import argparse
import json
from pathlib import Path

import cadquery as cq

from zcad.generators.tray import (
    TrayParameters,
    build_tray,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "design",
        type=Path,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("exports"),
    )
    args = parser.parse_args()

    with args.design.open(
        encoding="utf-8",
    ) as handle:
        design = json.load(handle)

    if design["type"] != "tray":
        raise ValueError(
            f"Unsupported design type: {design['type']}"
        )

    parameters = TrayParameters(
        **design["parameters"]
    )
    model = build_tray(parameters)
    solid = model.val()

    if not solid.isValid():
        raise ValueError(
            "Generated geometry is invalid"
        )

    args.output.mkdir(
        parents=True,
        exist_ok=True,
    )

    name = design["name"]
    step_path = args.output / f"{name}.step"
    stl_path = args.output / f"{name}.stl"

    cq.exporters.export(
        model,
        str(step_path),
    )
    cq.exporters.export(
        model,
        str(stl_path),
    )

    bounds = solid.BoundingBox()

    print(f"Generated: {name}")
    print(f"Valid solid: {solid.isValid()}")
    print(f"Volume: {solid.Volume():.2f} mm^3")
    print(
        "Bounds: "
        f"{bounds.xlen:.2f} × "
        f"{bounds.ylen:.2f} × "
        f"{bounds.zlen:.2f} mm"
    )
    print(f"STEP: {step_path}")
    print(f"STL:  {stl_path}")


if __name__ == "__main__":
    main()
