"""Connected garden layouts and separate-component STEP previews."""

import argparse
import hashlib
import json
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path

import cadquery as cq

from zcad.generators.garden_insertion import insertion_plan
from zcad.generators.pixel_garden_module import (
    PixelGardenModuleParameters,
    build_module,
)
from zcad.generators.pixel_grid import PixelGrid

COLLISION_TOLERANCE_MM3 = 1e-6
MAX_MODULES = 64


def build_garden_assembly(spec: dict) -> tuple[cq.Assembly, dict]:
    """Build a cup-up, unrotated layout; reject disconnected or colliding parts."""
    if not isinstance(spec, dict) or set(spec) - {"pattern", "module_parameters"}:
        raise ValueError("Expected pattern and optional module_parameters only")
    rows = spec.get("pattern")
    if (
        not isinstance(rows, list)
        or not rows
        or len(rows) > 64
        or any(not isinstance(row, str) or not row or len(row) > 64 for row in rows)
        or len({len(row) for row in rows}) != 1
        or any(set(row) - {"X", "."} for row in rows)
    ):
        raise ValueError("pattern must be rectangular X/. strings, at most 64 by 64")
    raw = spec.get("module_parameters", {})
    if not isinstance(raw, dict):
        raise ValueError("module_parameters must be an object")
    parameters = PixelGardenModuleParameters(**raw)
    parameters.validate()
    grid = PixelGrid(tuple(rows), parameters.size)
    cells = grid.filled_pixels()
    if not 1 <= len(cells) <= MAX_MODULES:
        raise ValueError(f"pattern must contain 1 to {MAX_MODULES} modules")
    seen = {min(cells)}
    pending = list(seen)
    while pending:
        r, c = pending.pop()
        for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if cell in cells and cell not in seen:
                seen.add(cell)
                pending.append(cell)
    if seen != cells:
        raise ValueError("Every module must connect through shared edges")

    module = build_module(parameters).val()
    assembly = cq.Assembly(name="garden")
    placed = []
    instances = []
    names = {}
    for r, c in sorted(cells):
        name = f"module_r{r:02d}_c{c:02d}"
        names[r, c] = name
        x, y = grid.pixel_center((r, c))
        assembly.add(module, name=name, loc=cq.Location(cq.Vector(x, y, 0)))
        placed.append(module.translate((x, y, 0)))
        instances.append(
            {"name": name, "row": r, "column": c, "position_mm": [x, y, 0]}
        )

    tested = 0
    for i, left in enumerate(placed):
        a = left.BoundingBox()
        for j in range(i + 1, len(placed)):
            right = placed[j]
            b = right.BoundingBox()
            if any(
                getattr(a, axis + "max") <= getattr(b, axis + "min")
                or getattr(b, axis + "max") <= getattr(a, axis + "min")
                for axis in "xyz"
            ):
                continue
            tested += 1
            overlap = left.intersect(right).Volume()
            if overlap > COLLISION_TOLERANCE_MM3:
                raise ValueError(
                    f"Collision: {instances[i]['name']} / {instances[j]['name']}: "
                    f"{overlap:.9g} mm^3"
                )
    connections = []
    for r, c in sorted(cells):
        for neighbor, male, female, axis in (
            ((r, c + 1), (r, c), (r, c + 1), "X"),
            ((r + 1, c), (r + 1, c), (r, c), "Y"),
        ):
            if neighbor in cells:
                connections.append(
                    {"male": names[male], "female": names[female], "axis": axis}
                )
    bounds = cq.Compound.makeCompound(placed).BoundingBox()
    report = {
        "schema_version": "1.1",
        "insertion_check": insertion_plan(module, instances),
        "module_count": len(cells),
        "unique_part_count": 1,
        "module_parameters": asdict(parameters),
        "pitch_mm": parameters.size,
        "bounds_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
        "instances": instances,
        "connection_count": len(connections),
        "connections": connections,
        "collision_check": {
            "status": "PASS",
            "candidate_pairs_tested": tested,
            "total_pairs": len(cells) * (len(cells) - 1) // 2,
            "volume_tolerance_mm3": COLLISION_TOLERANCE_MM3,
        },
        "scope": (
            "Nominal geometry and vertical insertion only; "
            "physical fit and strength unverified"
        ),
    }
    return assembly, report


def export_garden_assembly(source: Path, output: Path) -> dict:
    """Publish into a new directory; keep existing outputs untouched."""
    data = source.read_bytes()
    assembly, report = build_garden_assembly(json.loads(data))
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".garden-stage-", dir=output.parent
    ) as temp:
        stage = Path(temp)
        step = stage / "assembly.step"
        assembly.export(str(step), exportType="STEP", mode="default")
        (stage / "layout.json").write_bytes(data)
        report["artifacts"] = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (step, stage / "layout.json")
        }
        (stage / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        # Exclusive reservation prevents overwriting even an empty existing directory.
        output.mkdir()
        try:
            for path in stage.iterdir():
                shutil.copy2(path, output / path.name)
        except BaseException:
            shutil.rmtree(output)
            raise
    return report


def run_garden_assembly(arguments: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="zcad garden-assembly")
    parser.add_argument("layout", type=Path)
    parser.add_argument(
        "--output", required=True, type=Path, help="New output directory"
    )
    args = parser.parse_args(arguments)
    report = export_garden_assembly(args.layout, args.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    import sys

    run_garden_assembly(sys.argv[1:])
