"""Validate actual staged STL bytes and preserve destinations on failure."""

import hashlib
import json
import struct

import cadquery as cq
import pytest
from zcad_core.exporters import ExportRequest, export_parts
from zcad_core.validation.design_report import DesignValidationError
from zcad_core.validation.stl_mesh import read_stl

from zcad.feature_validation import feature_checks
from zcad.generators.tolerance_coupon import (
    ToleranceCouponParameters,
    build_tolerance_coupon,
)
from zcad.stl_features import stl_feature_checks


@pytest.fixture(scope="module")
def coupon():
    return build_tolerance_coupon(ToleranceCouponParameters([3.0], [3.0]))


def request(tmp_path, coupon):
    return ExportRequest(
        design_name="coupon",
        design_type="tolerance_coupon",
        parts={"main": coupon},
        output_directory=tmp_path / "exports",
        repository_root=tmp_path,
        parameters={"hole_diameters": [3.0], "slot_widths": [3.0]},
        feature_validator=feature_checks,
        stl_feature_validator=stl_feature_checks,
    )


def test_roundtrip_hash_and_metadata(tmp_path, coupon):
    result = export_parts(request(tmp_path, coupon))
    report = result.validation_report["stl_round_trip"]
    assert report["status"] == "PASS"
    assert len(report["checks"]) == 5
    assert all(c["status"] == "PASS" for c in report["checks"])
    part = result.parts[0]
    assert (
        report["stl_sha256_by_part"]["main"]
        == hashlib.sha256(part.stl_path.read_bytes()).hexdigest()
    )
    assert (
        json.loads(part.metadata_path.read_text())["design_validation"]
        == result.validation_report
    )


@pytest.mark.parametrize(
    "damage", ["blocked", "oversized", "truncated", "open", "reversed"]
)
@pytest.mark.parametrize("existing", [False, True])
def test_corruption_blocks_publication(tmp_path, coupon, monkeypatch, damage, existing):
    from pathlib import Path

    original = cq.exporters.export

    def corrupt(shape, path, *args, **kwargs):
        if str(path).endswith(".stl"):
            if damage == "blocked":
                shape = coupon.union(
                    cq.Workplane().box(4, 4, 1).translate((0, 9, 0))
                ).val()
            elif damage == "oversized":
                shape = coupon.cut(
                    cq.Workplane()
                    .circle(1.8)
                    .extrude(5, both=True)
                    .translate((0, 9, 0))
                ).val()
        original(shape, path, *args, **kwargs)
        if not str(path).endswith(".stl"):
            return
        p = Path(path)
        data = bytearray(p.read_bytes())
        if damage == "truncated":
            data = data[:-1]
        elif damage == "open":
            struct.pack_into("<I", data, 80, struct.unpack_from("<I", data, 80)[0] - 1)
            data = data[:-50]
        elif damage == "reversed":
            data[108:120], data[120:132] = data[120:132], data[108:120]
        p.write_bytes(data)

    req = request(tmp_path, coupon)
    if existing:
        req.output_directory.mkdir()
        (req.output_directory / "prior.txt").write_bytes(b"unchanged")
    monkeypatch.setattr(cq.exporters, "export", corrupt)
    with pytest.raises(DesignValidationError) as caught:
        export_parts(req)
    assert (
        "STL" in str(caught.value) or caught.value.report["evaluated_status"] == "FAIL"
    )
    if existing:
        assert {p.name: p.read_bytes() for p in req.output_directory.iterdir()} == {
            "prior.txt": b"unchanged"
        }
    else:
        assert not req.output_directory.exists()


def test_parser_and_occupancy(tmp_path):
    path = tmp_path / "box.stl"
    cq.exporters.export(cq.Workplane().box(4, 4, 4), str(path))
    mesh, check = read_stl(path.read_bytes())
    assert check["status"] == "PASS"
    assert mesh.contains((0, 0, 0))
    assert not mesh.contains((5, 0, 0))
    for data in (b"", b"solid ascii STL\nendsolid", path.read_bytes() + b"extra"):
        with pytest.raises(ValueError):
            read_stl(data)


def test_unsupported_is_explicit():
    assert (
        stl_feature_checks(design_type="other", parts={}, parameters={})[0]["status"]
        == "NOT_CHECKED"
    )
