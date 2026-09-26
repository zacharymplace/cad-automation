import ast
import hashlib
import json
from pathlib import Path

import cadquery as cq
import pytest

from zcad.generators import pixel_garden_assembly as garden


@pytest.mark.parametrize(
    "pattern,count,connections",
    [
        (["X"], 1, 0),
        (["XX", "XX"], 4, 4),
        (["XX", "X."], 3, 2),
        (["XXX", "X.X", "XXX"], 8, 8),
    ],
)
def test_layouts(pattern, count, connections):
    assembly, report = garden.build_garden_assembly({"pattern": pattern})
    assert len(assembly.toCompound().Solids()) == count
    assert report["module_count"] == count
    assert report["connection_count"] == connections
    assert report["collision_check"]["status"] == "PASS"


def test_coordinates_and_connection_direction():
    _, report = garden.build_garden_assembly({"pattern": ["XX", "X."]})
    assert [i["position_mm"] for i in report["instances"]] == [
        [-20, 20, 0],
        [20, 20, 0],
        [-20, -20, 0],
    ]
    assert report["connections"] == [
        {"male": "module_r00_c00", "female": "module_r00_c01", "axis": "X"},
        {"male": "module_r01_c00", "female": "module_r00_c00", "axis": "Y"},
    ]


@pytest.mark.parametrize(
    "pattern",
    [
        [],
        [""],
        [".."],
        ["X", "XX"],
        ["x"],
        ["X "],
        ["X.X"],
        ["X.", ".X"],
        [1],
        "X",
        ["X" * 65],
        ["XXXXXXXXX"] * 8,
    ],
)
def test_bad_patterns(pattern):
    with pytest.raises(ValueError):
        garden.build_garden_assembly({"pattern": pattern})


def test_collision_detection(monkeypatch):
    monkeypatch.setattr(
        garden, "build_module", lambda p: cq.Workplane().box(50, 50, 40)
    )
    with pytest.raises(ValueError, match="Collision"):
        garden.build_garden_assembly({"pattern": ["XX"]})


def test_export_round_trip_and_no_overwrite(tmp_path):
    source = tmp_path / "input.json"
    source.write_text(json.dumps({"pattern": ["XX", "X."]}))
    output = tmp_path / "assembly"
    report = garden.export_garden_assembly(source, output)
    shape = cq.importers.importStep(str(output / "assembly.step"))
    assert len(shape.solids().vals()) == 3
    bounds = shape.val().BoundingBox()
    assert [bounds.xlen, bounds.ylen, bounds.zlen] == pytest.approx(report["bounds_mm"])
    assert json.loads((output / "report.json").read_text()) == report
    for name, digest in report["artifacts"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    with pytest.raises(FileExistsError):
        garden.export_garden_assembly(source, output)
    assert json.loads((output / "report.json").read_text()) == report


def test_cli_dispatch(monkeypatch):
    # Execute the actual dispatcher without importing unrelated CAD generators.
    cli = Path(__file__).parents[1] / "src/zcad/cli.py"
    tree = ast.parse(cli.read_text())
    run = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run"
    )
    namespace = {}
    exec(compile(ast.Module(body=[run], type_ignores=[]), str(cli), "exec"), namespace)
    calls = []
    monkeypatch.setattr(garden, "run_garden_assembly", calls.append)
    namespace["run"](["garden-assembly", "layout.json", "--output", "out"])
    assert calls == [["layout.json", "--output", "out"]]
