"""Revision-bound digital acceptance for the Pico calibration enclosure."""

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from dataclasses import asdict, fields
from importlib.metadata import version
from pathlib import Path

import cadquery as cq
import numpy as np
import zcad_core
from zcad_core.features import DisplayWindowParameters
from zcad_core.validation.export_geometry import inspect_export_geometry
from zcad_core.validation.stl_mesh import read_stl

from zcad.assemblies.board_display import analyze_board_display_product
from zcad.generators.calibration.pico2_enclosure_fit import (
    Pico2EnclosureFitParameters,
    UsbPlugEnvelope,
    _analyze_usb_access_clearance,
    build_pico2_enclosure_fit,
)
from zcad.run_integrity import fingerprint
from zcad.validation_policy import evaluate_policy, load_policy

VOLUME_TOLERANCE_MM3 = 1e-6
STL_GEOMETRY_SAMPLE_COUNT = 2048
STL_GEOMETRY_VOLUME_FRACTION_TOLERANCE = 0.005


def _stl_geometry_tolerance(source_volume):
    return max(0.01, source_volume * STL_GEOMETRY_VOLUME_FRACTION_TOLERANCE)


def _halton_value(index, base):
    value = 0.0
    fraction = 1.0 / base
    while index:
        value += fraction * (index % base)
        index //= base
        fraction /= base
    return value


def _mesh_contains_points(triangles, points):
    """Vectorized two-ray parity for deterministic points away from facets."""
    answers = []
    triangle_a = triangles[:, 0, :]
    edge_1 = triangles[:, 1, :] - triangle_a
    edge_2 = triangles[:, 2, :] - triangle_a
    for direction in (
        np.asarray((0.137, 0.319, 1.0)),
        np.asarray((0.271, 1.0, 0.173)),
    ):
        h = np.cross(np.broadcast_to(direction, edge_2.shape), edge_2)
        determinant = np.einsum("ij,ij->i", edge_1, h)
        usable = np.abs(determinant) > 1e-12
        inverse = np.zeros_like(determinant)
        inverse[usable] = 1.0 / determinant[usable]
        hits = np.zeros(len(points), dtype=np.int64)
        for start in range(0, len(points), 16):
            batch = points[start : start + 16]
            offset = batch[:, None, :] - triangle_a[None, :, :]
            u = np.einsum("pti,ti->pt", offset, h) * inverse[None, :]
            q = np.cross(offset, edge_1[None, :, :])
            v = np.einsum("pti,i->pt", q, direction) * inverse[None, :]
            distance = np.einsum("pti,ti->pt", q, edge_2) * inverse[None, :]
            intersects = (
                usable[None, :] & (u >= 0) & (v >= 0) & (u + v <= 1) & (distance > 1e-9)
            )
            hits[start : start + len(batch)] = np.count_nonzero(intersects, axis=1)
        answers.append(hits % 2 == 1)
    if np.any(answers[0] != answers[1]):
        raise ValueError("Ambiguous STL point occupancy in geometry comparison")
    return answers[0]


def _sampled_stl_geometry_comparison(source_shape, mesh):
    """Estimate source/mesh symmetric difference by deterministic occupancy."""
    source_bounds = source_shape.BoundingBox()
    mesh_vertices = np.asarray(
        [vertex for triangle in mesh.triangles for vertex in triangle],
        dtype=np.float64,
    )
    low = np.minimum(
        np.asarray((source_bounds.xmin, source_bounds.ymin, source_bounds.zmin)),
        mesh_vertices.min(axis=0),
    )
    high = np.maximum(
        np.asarray((source_bounds.xmax, source_bounds.ymax, source_bounds.zmax)),
        mesh_vertices.max(axis=0),
    )
    extents = high - low
    points_unit = np.asarray(
        [
            (
                _halton_value(index, 2),
                _halton_value(index, 3),
                _halton_value(index, 5),
            )
            for index in range(1, STL_GEOMETRY_SAMPLE_COUNT + 1)
        ],
        dtype=np.float64,
    )
    points = low + points_unit * extents
    source_occupancy = np.fromiter(
        (source_shape.isInside(cq.Vector(*point), 1e-7) for point in points),
        dtype=np.bool_,
        count=len(points),
    )
    mesh_occupancy = _mesh_contains_points(
        np.asarray(mesh.triangles, dtype=np.float64), points
    )
    mismatch_count = int(np.count_nonzero(source_occupancy != mesh_occupancy))
    bounds_volume = float(np.prod(extents))
    estimate = bounds_volume * mismatch_count / len(points)
    return {
        "method": "deterministic Halton occupancy sampling; bases 2, 3, 5",
        "sample_count": len(points),
        "mismatching_samples": mismatch_count,
        "sampled_bounds_mm": [low.tolist(), high.tolist()],
        "estimated_symmetric_difference_volume_mm3": estimate,
        "estimated_mismatch_fraction": mismatch_count / len(points),
        "limitation": (
            "Approximate digital comparison; localized differences smaller than "
            "the sample spacing can be missed."
        ),
    }


def _source_state(package):
    root = Path(package).resolve().parent
    files = {
        str(path.relative_to(root)): fingerprint(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.suffix in {".py", ".json"}
    }
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    result = {"package_path": str(root), "source_sha256": digest, "files": files}
    for key, arguments in [
        ("head", ["rev-parse", "HEAD"]),
        ("working_tree", ["status", "--porcelain"]),
    ]:
        command = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        result[key] = command.stdout.strip() if command.returncode == 0 else None
    return result


def _sources():
    return {
        "product": _source_state(__file__),
        "core": _source_state(zcad_core.__file__),
    }


def _dimensions(shape):
    bounds = shape.BoundingBox()
    return {"x": bounds.xlen, "y": bounds.ylen, "z": bounds.zlen}


def _maximum_enclosure_envelope_check(assembled_dimensions, maximum):
    measured = {
        "width": assembled_dimensions["x"],
        "depth": assembled_dimensions["y"],
        "height": assembled_dimensions["z"],
    }
    tolerance = 1e-6
    exceeded = [
        name for name, value in measured.items() if value > maximum[name] + tolerance
    ]
    return {
        "code": "maximum_enclosure_envelope",
        "subject": "assembled",
        "status": "FAIL" if exceeded else "PASS",
        "measured_mm": measured,
        "maximum_mm": maximum,
        "exceedance_mm": {
            name: max(0.0, value - maximum[name]) for name, value in measured.items()
        },
        "tolerance_mm": tolerance,
        "exceeded_dimensions": exceeded,
    }


def _overlap(first, second):
    value = first.intersect(second).val().Volume()
    if not math.isfinite(value) or value < 0:
        raise ValueError("Invalid intersection evidence")
    return value


def _export_artifact_check(name, part, output, export_errors=None):
    """Validate exported bytes against their source geometry and record identity."""
    source_shape = part.val()
    source_bounds = source_shape.BoundingBox()
    source_dimensions = (source_bounds.xlen, source_bounds.ylen, source_bounds.zlen)
    source_volume = source_shape.Volume()
    exports = {}
    failures = []
    export_errors = export_errors or {}

    for extension in ("step", "stl"):
        path = output / f"{name}.{extension}"
        try:
            data = path.read_bytes()
        except OSError as error:
            missing_reason = f"Export file unavailable: {error}"
            if extension in export_errors:
                missing_reason = f"{export_errors[extension]}; {missing_reason}"
            record = {
                "path": path.name,
                "size_bytes": 0,
                "sha256": None,
                "status": "FAIL",
                "error": missing_reason,
            }
            exports[extension] = record
            failures.append(f"{path.name}: {record['error']}")
            continue
        record = {
            "path": path.name,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        try:
            if extension in export_errors:
                raise ValueError(export_errors[extension])
            if not data:
                raise ValueError("Export is empty")
            if extension == "step":
                imported = cq.importers.importStep(str(path))
                inspection = inspect_export_geometry(imported, name)
                dimension_errors = [
                    abs(actual - expected)
                    for actual, expected in zip(
                        inspection.bounds_mm, source_dimensions, strict=True
                    )
                ]
                volume_error = abs(inspection.volume_mm3 - source_volume)
                imported_shape = imported.solids().val()
                source_only_volume = source_shape.cut(imported_shape).Volume()
                imported_only_volume = imported_shape.cut(source_shape).Volume()
                symmetric_difference_volume = source_only_volume + imported_only_volume
                volume_tolerance = max(1e-5, source_volume * 1e-6)
                passed = (
                    inspection.report["solid_count"] == 1
                    and max(dimension_errors) <= 0.01
                    and volume_error <= volume_tolerance
                    and symmetric_difference_volume <= volume_tolerance
                )
                record.update(
                    {
                        "solid_count": inspection.report["solid_count"],
                        "dimensions_mm": list(inspection.bounds_mm),
                        "volume_mm3": inspection.volume_mm3,
                        "source_volume_mm3": source_volume,
                        "max_dimension_difference_mm": max(dimension_errors),
                        "volume_difference_mm3": volume_error,
                        "symmetric_difference_volume_mm3": symmetric_difference_volume,
                        "source_only_volume_mm3": source_only_volume,
                        "imported_only_volume_mm3": imported_only_volume,
                        "round_trip_tolerance": {
                            "dimensions_mm": 0.01,
                            "volume_mm3": volume_tolerance,
                            "symmetric_difference_volume_mm3": volume_tolerance,
                        },
                    }
                )
                if not passed:
                    raise ValueError("STEP geometry differs from source geometry")
            else:
                mesh, topology = read_stl(data)
                vertices = [v for triangle in mesh.triangles for v in triangle]
                mesh_dimensions = [
                    max(vertex[axis] for vertex in vertices)
                    - min(vertex[axis] for vertex in vertices)
                    for axis in range(3)
                ]
                dimension_errors = [
                    abs(actual - expected)
                    for actual, expected in zip(
                        mesh_dimensions, source_dimensions, strict=True
                    )
                ]
                mesh_volume = topology["signed_volume_mm3"]
                volume_error = abs(mesh_volume - source_volume)
                volume_tolerance = max(0.01, source_volume * 0.02)
                geometry_tolerance = _stl_geometry_tolerance(source_volume)
                geometry_comparison = _sampled_stl_geometry_comparison(
                    source_shape, mesh
                )
                dimensions_ok = max(dimension_errors) <= 0.05
                geometry_error = geometry_comparison[
                    "estimated_symmetric_difference_volume_mm3"
                ]
                passed = (
                    dimensions_ok
                    and volume_error <= volume_tolerance
                    and geometry_error <= geometry_tolerance
                )
                record.update(
                    {
                        "triangle_count": topology["triangle_count"],
                        "dimensions_mm": mesh_dimensions,
                        "volume_mm3": mesh_volume,
                        "source_volume_mm3": source_volume,
                        "max_dimension_difference_mm": max(dimension_errors),
                        "volume_difference_mm3": volume_error,
                        "geometry_comparison": geometry_comparison,
                        "tolerance": {
                            "dimensions_mm": 0.05,
                            "volume_mm3": volume_tolerance,
                            "estimated_symmetric_difference_volume_mm3": (
                                geometry_tolerance
                            ),
                            "topology": topology["message"],
                        },
                    }
                )
                if not passed:
                    raise ValueError("STL geometry differs from source geometry")
            record["status"] = "PASS"
        except Exception as error:
            record["status"] = "FAIL"
            record["error"] = str(error)
            failures.append(f"{path.name}: {error}")
        exports[extension] = record

    return {
        "code": "export_artifact_integrity",
        "subject": name,
        "status": "FAIL" if failures else "PASS",
        "source_dimensions_mm": list(source_dimensions),
        "source_volume_mm3": source_volume,
        "exports": exports,
        "failures": failures,
    }


def _geometry_checks(parameters, parts):
    checks = []

    def volume_check(code, value, **details):
        checks.append(
            {
                "code": code,
                "status": "PASS" if value <= VOLUME_TOLERANCE_MM3 else "FAIL",
                "residual_material_mm3": value,
                "tolerance_mm3": VOLUME_TOLERANCE_MM3,
                **details,
            }
        )

    for name, part in parts.items():
        inspection = inspect_export_geometry(part, name)
        checks.append(
            {
                "code": "valid_single_solid",
                "subject": name,
                "status": "PASS" if len(inspection.shape.Solids()) == 1 else "FAIL",
            }
        )
    display_bounds = (
        parameters.device_assembly.get("display")
        .transformed_geometry()
        .val()
        .BoundingBox()
    )
    for component in parameters.device_assembly:
        if component.identifier in {"display", "usb_connector"}:
            continue
        bounds = component.transformed_geometry().val().BoundingBox()
        if (
            bounds.xmin < display_bounds.xmax
            and bounds.xmax > display_bounds.xmin
            and bounds.ymin < display_bounds.ymax
            and bounds.ymax > display_bounds.ymin
        ):
            checks.append(
                {
                    "code": "display_vertical_gap",
                    "subject": component.identifier,
                    "status": "PASS"
                    if display_bounds.zmin - bounds.zmax + 1e-9
                    >= parameters.board_display_clearance_mm
                    else "FAIL",
                    "measured_gap_mm": display_bounds.zmin - bounds.zmax,
                    "required_gap_mm": parameters.board_display_clearance_mm,
                    "method": "conservative bounding-box vertical gap",
                }
            )
    report = analyze_board_display_product(
        parameters.product,
        parameters.device_assembly,
        minimum_board_display_clearance_mm=parameters.board_display_clearance_mm,
    )
    checks.append(
        {
            "code": "hardware_collision_and_clearance",
            "status": "FAIL" if report.has_findings else "PASS",
            "required_board_display_clearance_mm": (
                parameters.board_display_clearance_mm
            ),
            "findings": [asdict(finding) for finding in report.findings],
        }
    )
    access = _analyze_usb_access_clearance(parameters)
    checks.append(
        {
            "code": "usb_boundary_clearance",
            "status": "FAIL" if access.has_findings else "PASS",
            "required_access_clearance_mm": parameters.usb_access_clearance_mm,
            "findings": [asdict(finding) for finding in access.findings],
        }
    )
    seated = parts["lid"].translate(
        (0, 0, parameters.body_height_mm - parameters.lid_lip_height_mm)
    )
    for component in parameters.device_assembly:
        for name, part in [("body", parts["body"]), ("seated_lid", seated)]:
            volume_check(
                "hardware_enclosure_collision",
                _overlap(part, component.transformed_geometry()),
                subject=f"{component.identifier}/{name}",
            )
    volume_check(
        "lid_seating_collision",
        _overlap(parts["body"], seated),
        seating_z_mm=parameters.body_height_mm - parameters.lid_lip_height_mm,
    )
    board = parameters.product.board
    for x in [
        -board.mounting_hole_spacing_x_mm / 2,
        board.mounting_hole_spacing_x_mm / 2,
    ]:
        for y in [
            -board.mounting_hole_spacing_y_mm / 2,
            board.mounting_hole_spacing_y_mm / 2,
        ]:
            probe = (
                cq.Workplane("XY")
                .circle(board.mounting_hole_diameter_mm / 2)
                .extrude(parameters.standoff_height_mm)
                .translate((x, y, parameters.floor_mm))
            )
            volume_check(
                "mounting_bore_alignment",
                _overlap(parts["body"], probe),
                center_mm=[x, y],
            )
    window = DisplayWindowParameters.from_display(
        display=parameters.display_spec,
        panel_base_z_mm=parameters.lid_lip_height_mm,
        panel_thickness_mm=parameters.lid_thickness_mm,
        x=parameters.display_center_x_mm,
        y=parameters.display_center_y_mm,
        window_clearance_mm=parameters.display_window_clearance_mm,
        corner_radius_mm=parameters.display_window_corner_radius_mm,
    )
    # Probe the declared rounded window, including its clearance and raised bezel.
    probe = (
        cq.Workplane("XY")
        .rect(window.opening_width_mm, window.opening_height_mm)
        .extrude(parameters.lid_thickness_mm + parameters.display_bezel_height_mm)
    )
    if window.corner_radius_mm > 0:
        probe = probe.edges("|Z").fillet(window.corner_radius_mm)
    probe = probe.translate((window.x, window.y, window.panel_base_z_mm))
    volume_check(
        "display_window_opening",
        _overlap(parts["lid"], probe),
        center_mm=[window.x, window.y],
        opening_mm=[window.opening_width_mm, window.opening_height_mm],
    )
    connector = parameters.device_assembly.get("usb_connector")
    bounds = connector.transformed_geometry().val().BoundingBox()
    outer_y = -parameters.outer_depth_mm / 2 - 1
    depth = bounds.ymin - outer_y
    if depth <= 0:
        raise ValueError("USB access probe has no outward path")
    probe = (
        cq.Workplane("XY")
        .box(bounds.xlen, depth, bounds.zlen, centered=(True, True, False))
        .translate(
            ((bounds.xmin + bounds.xmax) / 2, (outer_y + bounds.ymin) / 2, bounds.zmin)
        )
    )
    volume_check("usb_connector_sized_straight_path", _overlap(parts["body"], probe))
    if parameters.usb_plug is None:
        checks.extend(
            [
                {
                    "code": "usb_plug_geometry",
                    "status": "NOT_CHECKED",
                    "reason": "No plug housing specification was supplied.",
                },
                {
                    "code": "usb_plug_insertion_path",
                    "status": "NOT_CHECKED",
                    "reason": "No plug housing specification was supplied.",
                },
                {
                    "code": "cable_bend_clearance",
                    "status": "NOT_CHECKED",
                    "reason": "Cable and strain-relief bend envelope not supplied.",
                },
            ]
        )
    else:
        plug = parameters.usb_plug
        if not isinstance(plug, UsbPlugEnvelope):
            raise ValueError("Invalid normalized USB plug specification")
        if parameters.product.board.usb_connector.board_edge != "negative_y":
            raise ValueError(
                "USB plug insertion currently supports the Pico negative-Y port"
            )
        port = (
            parameters.device_assembly.get("usb_connector")
            .transformed_geometry()
            .val()
            .BoundingBox()
        )
        center_x = (port.xmin + port.xmax) / 2
        port_center_z = (port.zmin + port.zmax) / 2
        housing_center_z = port_center_z + plug.center_height_offset_mm
        nose_center_z = port_center_z + plug.nose_center_height_offset_mm
        outer_face_y = -parameters.outer_depth_mm / 2
        housing = (
            cq.Workplane("XY")
            .box(
                plug.width_mm,
                plug.housing_length_mm,
                plug.height_mm,
                centered=(True, True, True),
            )
            .translate(
                (center_x, outer_face_y - plug.housing_length_mm / 2, housing_center_z)
            )
        )
        housing_body_overlap = _overlap(parts["body"], housing)
        occupied = []
        for component in parameters.device_assembly:
            if component.identifier == "usb_connector":
                continue
            overlap = _overlap(housing, component.transformed_geometry())
            if overlap > VOLUME_TOLERANCE_MM3:
                occupied.append(
                    {"component": component.identifier, "intersection_mm3": overlap}
                )
        checks.append(
            {
                "code": "usb_plug_housing_fit",
                "status": "PASS"
                if housing_body_overlap <= VOLUME_TOLERANCE_MM3 and not occupied
                else "FAIL",
                "plug": asdict(plug),
                "housing_intersection_with_body_mm3": housing_body_overlap,
                "hardware_intersections": occupied,
                "method": "rectangular overmold placed outside the enclosure wall",
            }
        )
        nose = (
            cq.Workplane("XY")
            .box(
                plug.nose_width_mm,
                plug.nose_length_mm,
                plug.nose_height_mm,
                centered=(True, True, True),
            )
            .translate(
                (center_x, outer_face_y + plug.nose_length_mm / 2, nose_center_z)
            )
        )
        nose_body_overlap = _overlap(parts["body"], nose)
        nose_hits = []
        for component in parameters.device_assembly:
            if component.identifier == "usb_connector":
                continue
            overlap = _overlap(nose, component.transformed_geometry())
            if overlap > VOLUME_TOLERANCE_MM3:
                nose_hits.append(
                    {"component": component.identifier, "intersection_mm3": overlap}
                )
        connector_overlap = _overlap(
            nose, parameters.device_assembly.get("usb_connector").transformed_geometry()
        )
        connector_fit = (
            nose.val().BoundingBox().xmin >= port.xmin
            and nose.val().BoundingBox().xmax <= port.xmax
            and nose.val().BoundingBox().zmin >= port.zmin
            and nose.val().BoundingBox().zmax <= port.zmax
            and connector_overlap > VOLUME_TOLERANCE_MM3
        )
        checks.append(
            {
                "code": "usb_plug_nose_mates_with_receptacle",
                "status": "PASS"
                if connector_fit
                and nose_body_overlap <= VOLUME_TOLERANCE_MM3
                and not nose_hits
                else "FAIL",
                "nose_intersection_with_receptacle_mm3": connector_overlap,
                "nose_intersection_with_body_mm3": nose_body_overlap,
                "other_hardware_intersections": nose_hits,
                "method": "nose envelope contained by modeled receptacle width/height",
            }
        )
        port_travel = max(2.0, abs(port.ymin - outer_face_y) + 1.0)
        housing_sweep = (
            cq.Workplane("XY")
            .box(
                plug.width_mm,
                plug.housing_length_mm + port_travel,
                plug.height_mm,
                centered=(True, True, True),
            )
            .translate(
                (
                    center_x,
                    outer_face_y - (plug.housing_length_mm + port_travel) / 2,
                    housing_center_z,
                )
            )
        )
        nose_sweep_length = plug.nose_length_mm + port_travel
        nose_sweep = (
            cq.Workplane("XY")
            .box(
                plug.nose_width_mm,
                nose_sweep_length,
                plug.nose_height_mm,
                centered=(True, True, True),
            )
            .translate(
                (
                    center_x,
                    outer_face_y + plug.nose_length_mm / 2 - port_travel / 2,
                    nose_center_z,
                )
            )
        )
        path_body_overlap = _overlap(parts["body"], housing_sweep) + _overlap(
            parts["body"], nose_sweep
        )
        path_hits = []
        for component in parameters.device_assembly:
            if component.identifier == "usb_connector":
                continue
            overlap = _overlap(
                housing_sweep, component.transformed_geometry()
            ) + _overlap(nose_sweep, component.transformed_geometry())
            if overlap > VOLUME_TOLERANCE_MM3:
                path_hits.append(
                    {"component": component.identifier, "intersection_mm3": overlap}
                )
        checks.append(
            {
                "code": "usb_plug_insertion_path",
                "status": "PASS"
                if path_body_overlap <= VOLUME_TOLERANCE_MM3
                and not path_hits
                and connector_fit
                else "FAIL",
                "translation_mm": [0.0, port_travel, 0.0],
                "housing_sweep_length_mm": plug.housing_length_mm + port_travel,
                "nose_sweep_length_mm": nose_sweep_length,
                "housing_path_intersection_with_body_mm3": _overlap(
                    parts["body"], housing_sweep
                ),
                "nose_path_intersection_with_body_mm3": _overlap(
                    parts["body"], nose_sweep
                ),
                "other_hardware_intersections": path_hits,
                "method": (
                    "continuous straight translation along negative Y; "
                    "nose seats in receptacle"
                ),
                "assumptions": [
                    "Housing and nose are axis-aligned rectangular envelopes.",
                    "Insertion is a straight translation with no tilt or rotation.",
                    "Receptacle bounds use its modeled axis-aligned bounding box.",
                    "USB receptacle contact at the seated nose is intentional.",
                    "Cable, strain relief, chamfers, latches, and manufacturing "
                    "variation are omitted.",
                ],
                "scope_limit": (
                    "PASS covers only this nominal envelope sweep; it does not "
                    "establish real-cable or physical insertion."
                ),
            }
        )
        checks.append(
            {
                "code": "cable_bend_clearance",
                "status": "NOT_CHECKED",
                "reason": "Flexible cable and bend envelope were not supplied.",
            }
        )
    if parameters.display_retention == "clips":
        engagement = []
        geometry = parameters.device_assembly.get("display").transformed_geometry()
        for name, translation in [
            ("negative_x", (-parameters.retention_clearance_mm - 0.1, 0, 0)),
            ("positive_x", (parameters.retention_clearance_mm + 0.1, 0, 0)),
            ("negative_y", (0, -parameters.retention_clearance_mm - 0.1, 0)),
            ("positive_y", (0, parameters.retention_clearance_mm + 0.1, 0)),
            ("negative_z", (0, 0, -parameters.retention_clip_gap_mm - 0.1)),
            ("positive_z", (0, 0, 0.1)),
        ]:
            overlap = _overlap(seated, geometry.translate(translation))
            engagement.append(
                {
                    "direction": name,
                    "translation_mm": translation,
                    "stop_intersection_mm3": overlap,
                    "status": "PASS" if overlap > VOLUME_TOLERANCE_MM3 else "FAIL",
                }
            )
        checks.append(
            {
                "code": "oled_retention",
                "status": "PASS"
                if all(probe["status"] == "PASS" for probe in engagement)
                else "FAIL",
                "method": "six cardinal translation stop probes",
                "parameters": asdict(parameters.retention_parameters),
                "probes": engagement,
            }
        )
    else:
        checks.append(
            {
                "code": "oled_retention",
                "status": "NOT_CHECKED",
                "reason": "display_retention is none",
            }
        )
    checks.extend(
        [
            {
                "code": "actual_cable_plug_access",
                "status": "NOT_CHECKED",
                "reason": "Cable plug and bend envelope not supplied.",
            },
            {
                "code": "clip_flex_and_holding_strength",
                "status": "NOT_CHECKED",
                "reason": "Clip behavior and load capacity require physical tests.",
            },
            {
                "code": "printed_fit",
                "status": "NOT_CHECKED",
                "reason": "Digital geometry cannot establish physical fit.",
            },
        ]
    )
    return checks, seated


def _write_summary(folder, report):
    profile = report["acceptance_profile"]
    required_checks = profile["policy"]["required_checks"] if profile["policy"] else []
    lines = [
        f"# Enclosure acceptance: {report['revision']}",
        "",
        f"Digital result: **{report['digital_status']}**",
        "",
        "Physical testing: **PENDING**. Digital results do not certify printed fit.",
        "",
        f"Acceptance profile: **{profile['identifier']}** ({profile['status']})",
        "Required checks: " + (", ".join(required_checks) or "unavailable"),
        "",
        f"Design SHA-256: `{report['design']['sha256']}`",
        "",
        "| Check | Result | Subject / reason |",
        "| --- | --- | --- |",
    ]
    maximum_envelope = profile["policy"].get("maximum_enclosure_envelope_mm")
    if maximum_envelope is not None:
        lines.insert(
            7,
            "Maximum assembled envelope (mm): "
            f"{maximum_envelope['width']:.3f} × "
            f"{maximum_envelope['depth']:.3f} × "
            f"{maximum_envelope['height']:.3f}",
        )
    for check in report["checks"]:
        detail = check.get("subject", check.get("reason", check.get("message", "")))
        if check["code"] == "maximum_enclosure_envelope":
            measured = check["measured_mm"]
            detail = (
                f"{measured['width']:.3f} × {measured['depth']:.3f} × "
                f"{measured['height']:.3f} mm; limits "
                f"{maximum_envelope['width']:.3f} × "
                f"{maximum_envelope['depth']:.3f} × "
                f"{maximum_envelope['height']:.3f} mm"
            )
            if check["exceeded_dimensions"]:
                detail += "; exceeds " + ", ".join(check["exceeded_dimensions"])
        if check["code"] == "acceptance_profile" and check.get("reasons"):
            detail = "; ".join(check["reasons"])
        detail = str(detail).replace("|", "/").replace(chr(10), " ")
        lines.append(f"| {check['code']} | {check['status']} | {detail} |")
        if check["code"] == "export_artifact_integrity":
            for _extension, artifact in check["exports"].items():
                lines.append(
                    f"| {artifact['path']} | {artifact['status']} | "
                    f"{artifact['size_bytes']} bytes; SHA-256 "
                    f"`{artifact['sha256']}` |"
                )
        if check["code"] == "usb_plug_insertion_path" and "method" in check:
            lines.extend(
                [
                    "",
                    f"USB insertion method: {check['method']}.",
                    "Assumptions: " + " ".join(check["assumptions"]),
                    f"Scope limit: {check['scope_limit']}",
                ]
            )
    if "dimensions_mm" in report:
        lines += ["", "| Geometry | Width × depth × height (mm) |", "| --- | --- |"]
        for name, size in report["dimensions_mm"].items():
            lines.append(
                f"| {name} | {size['x']:.3f} × {size['y']:.3f} × {size['z']:.3f} |"
            )
    if "hardware" in report:
        plug = report["hardware"].get("usb_plug")
        if plug:
            lines += [
                "",
                f"USB plug model: {plug['identifier']}",
                f"Plug evidence status (declared): {plug['evidence_status']}",
                f"Plug evidence source (declared): {plug['evidence_source']}",
            ]
        display = report["hardware"]["display"]
        lines += [
            "",
            f"Board: {report['hardware']['board']['identifier']}",
            f"Display: {display['identifier']}",
            "Display source (declared): "
            f"{display['geometry_source'] or 'vendor-neutral reference'}",
            f"Display evidence label (declared): {display['geometry_evidence_status']}",
        ]
    lines += [
        "",
        f"Product HEAD: {report['sources']['product']['head']}",
        f"Core HEAD: {report['sources']['core']['head']}",
        "Exact source-file hashes and working-tree state are retained in report.json.",
    ]
    lines += [
        "",
        "See report.json for dimensions, hardware, source hashes, and measurements.",
        "",
        "Scope: nominal CAD assembly only. Actual hardware, printed fit, cable bends, "
        "physical retention strength and customer acceptance remain separate evidence.",
    ]
    (folder / "report.md").write_text("\n".join(lines) + "\n")


def build_acceptance(design_path, output, revision, *, profile_path=None):
    """Build fresh evidence; never overwrite an existing revision folder."""
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError("revision must not be empty")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Acceptance output must be an empty directory")
    raw = Path(design_path).read_bytes()
    (output / "design.json").write_bytes(raw)
    if profile_path is None:
        profile_path = (
            Path(__file__).resolve().parents[2]
            / "designs/acceptance-profiles/pico2-digital-baseline.json"
        )
    profile_path = Path(profile_path)
    profile_bytes = profile_path.read_bytes()
    (output / "acceptance-profile.json").write_bytes(profile_bytes)
    sources = _sources()
    report = {
        "schema_version": "1.0",
        "revision": revision,
        "digital_status": "REVISION_REQUIRED",
        "physical_status": "PENDING",
        "scope": "Pico calibration nominal CAD assembly",
        "acceptance_profile": {
            "identifier": profile_path.stem,
            "path": str(profile_path.resolve()),
            "sha256": hashlib.sha256(profile_bytes).hexdigest(),
            "policy": None,
            "status": "REVISION_REQUIRED",
            "reasons": [],
        },
        "design": {
            "path": str(Path(design_path).resolve()),
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "sources": sources,
        "software": {
            "python": sys.version,
            "cadquery": version("cadquery"),
            "zcad_core_distribution": version("zcad-core"),
        },
        "checks": [],
        "artifacts": {},
    }
    profile_policy = None
    try:
        profile_policy = load_policy(profile_path)
        report["acceptance_profile"]["policy"] = profile_policy
        document = json.loads(raw)
        if document["type"] != "pico2_enclosure_fit":
            raise ValueError("Acceptance currently supports pico2_enclosure_fit only")
        parameters = Pico2EnclosureFitParameters(**document["parameters"])
        for field in fields(parameters):
            value = getattr(parameters, field.name)
            if field.name not in {
                "display",
                "usb_plug",
                "label_text",
                "display_retention",
            } and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"{field.name} must be a finite number")
        report["hardware"] = {
            "board": asdict(parameters.product.board),
            "display": asdict(parameters.display_spec),
            "usb_plug": asdict(parameters.usb_plug) if parameters.usb_plug else None,
            "evidence_note": "Declared inputs; actual hardware has not been measured.",
        }
        catalog = (
            Path(zcad_core.__file__).parent
            / "hardware/data/board-components/raspberry-pi-pico-2.json"
        )
        report["hardware"]["board_component_catalog"] = json.loads(catalog.read_text())
        report["resolved_parameters"] = asdict(parameters)
        parts = build_pico2_enclosure_fit(parameters)
        report["checks"], seated = _geometry_checks(parameters, parts)
        report["dimensions_mm"] = {
            name: _dimensions(part.val()) for name, part in parts.items()
        }
        report["dimensions_mm"]["assembled"] = _dimensions(
            parts["body"].union(seated).val()
        )
        maximum_envelope = profile_policy.get("maximum_enclosure_envelope_mm")
        if maximum_envelope is not None:
            report["checks"].append(
                _maximum_enclosure_envelope_check(
                    report["dimensions_mm"]["assembled"], maximum_envelope
                )
            )
        report["hardware_placements"] = {
            component.identifier: asdict(component.placement)
            for component in parameters.device_assembly
        }
        if not any(check["status"] == "FAIL" for check in report["checks"]):
            artifact_checks = []
            for name, part in parts.items():
                export_errors = {}
                for extension in ("step", "stl"):
                    try:
                        cq.exporters.export(part, str(output / f"{name}.{extension}"))
                    except Exception as error:
                        export_errors[extension] = (
                            f"Exporter raised {type(error).__name__}: {error}"
                        )
                artifact_check = _export_artifact_check(
                    name, part, output, export_errors
                )
                artifact_checks.append(artifact_check)
            report["checks"].extend(artifact_checks)
            report["digital_status"] = (
                "DIGITAL_CHECKS_PASSED"
                if all(check["status"] == "PASS" for check in artifact_checks)
                else "REVISION_REQUIRED"
            )
    except Exception as error:
        # Geometry backends can raise RuntimeError as well as input errors.
        # Persist the failure and never label a partially built package accepted.
        report["digital_status"] = "REVISION_REQUIRED"
        report["checks"].append(
            {
                "code": "input_or_geometry",
                "status": "FAIL",
                "message": str(error),
                "error_type": type(error).__name__,
            }
        )
    after = _sources()
    if (
        after != sources
        or Path(design_path).read_bytes() != raw
        or profile_path.read_bytes() != profile_bytes
    ):
        report["digital_status"] = "REVISION_REQUIRED"
        report["checks"].append(
            {
                "code": "source_stability",
                "status": "FAIL",
                "message": "Source changed during the run; repeat the check.",
            }
        )
    else:
        report["checks"].append({"code": "source_stability", "status": "PASS"})
    if profile_policy is None:
        profile_result = {
            "status": "FAIL",
            "reasons": ["Acceptance profile could not be loaded"],
        }
    else:
        profile_result = evaluate_policy(
            {
                "checks": report["checks"],
                "evaluated_status": (
                    "FAIL"
                    if any(check.get("status") == "FAIL" for check in report["checks"])
                    else "PASS"
                ),
                "warning_count": 0,
            },
            profile_policy,
        )
    report["acceptance_profile"].update(
        {"status": profile_result["status"], "reasons": profile_result["reasons"]}
    )
    report["checks"].append(
        {
            "code": "acceptance_profile",
            "status": profile_result["status"],
            "profile": profile_path.stem,
            "required_checks": profile_policy["required_checks"]
            if profile_policy
            else [],
            "reasons": profile_result["reasons"],
        }
    )
    if profile_result["status"] != "PASS":
        report["digital_status"] = "REVISION_REQUIRED"
    _write_summary(output, report)
    report["artifacts"] = {
        path.name: fingerprint(path)
        for path in sorted(output.iterdir())
        if path.is_file()
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return report


def run_acceptance(arguments):
    parser = argparse.ArgumentParser(prog="zcad accept")
    parser.add_argument("design", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args(arguments)
    report = build_acceptance(
        args.design, args.output, args.revision, profile_path=args.profile
    )
    print(f"{report['digital_status']}: {args.output / 'report.md'}")
    if report["digital_status"] != "DIGITAL_CHECKS_PASSED":
        raise SystemExit(1)


def _report_consistency_failures(report, artifacts, folder):
    failures = []
    checks = report.get("checks")
    if not isinstance(checks, list):
        return ["checks must be a list"]

    for index, check in enumerate(checks):
        if not isinstance(check, dict) or check.get("status") not in {
            "PASS",
            "FAIL",
            "NOT_CHECKED",
        }:
            failures.append(f"checks[{index}] has an invalid status")

    outcome = report["digital_status"]
    if outcome == "DIGITAL_CHECKS_PASSED" and any(
        check.get("status") == "FAIL" for check in checks if isinstance(check, dict)
    ):
        failures.append("accepted outcome contains a failed check")

    export_checks = [
        check
        for check in checks
        if isinstance(check, dict) and check.get("code") == "export_artifact_integrity"
    ]
    seen_subjects = set()
    for check in export_checks:
        subject = check.get("subject")
        if subject not in {"body", "lid"} or subject in seen_subjects:
            failures.append(
                "export integrity checks have an invalid or duplicate subject"
            )
            continue
        seen_subjects.add(subject)
        exports = check.get("exports")
        if not isinstance(exports, dict) or set(exports) != {"step", "stl"}:
            failures.append(f"{subject} export check has an incomplete file list")
            continue
        statuses = []
        for extension, export in exports.items():
            if not isinstance(export, dict):
                failures.append(f"{subject}.{extension} export record is invalid")
                continue
            expected_name = f"{subject}.{extension}"
            size = export.get("size_bytes")
            digest = export.get("sha256")
            status = export.get("status")
            statuses.append(status)
            if export.get("path") != expected_name:
                failures.append(
                    f"{subject}.{extension} path does not match its subject"
                )
            if status not in {"PASS", "FAIL"}:
                failures.append(f"{expected_name} has an invalid export status")
            if extension == "stl" and "geometry_comparison" in export:
                comparison = export["geometry_comparison"]
                tolerance_record = export.get("tolerance", {})
                try:
                    sample_count = comparison["sample_count"]
                    mismatches = comparison["mismatching_samples"]
                    bounds = comparison["sampled_bounds_mm"]
                    estimate = comparison["estimated_symmetric_difference_volume_mm3"]
                    mismatch_fraction = comparison["estimated_mismatch_fraction"]
                    threshold = tolerance_record[
                        "estimated_symmetric_difference_volume_mm3"
                    ]
                    if (
                        type(sample_count) is not int
                        or sample_count != STL_GEOMETRY_SAMPLE_COUNT
                        or type(mismatches) is not int
                        or not 0 <= mismatches <= sample_count
                        or not isinstance(bounds, list)
                        or len(bounds) != 2
                        or any(
                            not isinstance(point, list)
                            or len(point) != 3
                            or any(
                                isinstance(value, bool)
                                or not isinstance(value, (int, float))
                                or not math.isfinite(value)
                                for value in point
                            )
                            for point in bounds
                        )
                        or not all(
                            bounds[0][axis] < bounds[1][axis] for axis in range(3)
                        )
                        or any(
                            isinstance(value, bool)
                            or not isinstance(value, (int, float))
                            or not math.isfinite(value)
                            for value in (estimate, mismatch_fraction, threshold)
                        )
                        or threshold <= 0
                        or not isinstance(comparison.get("method"), str)
                        or not isinstance(comparison.get("limitation"), str)
                    ):
                        raise ValueError
                    bounds_volume = math.prod(
                        bounds[1][axis] - bounds[0][axis] for axis in range(3)
                    )
                    expected_estimate = bounds_volume * mismatches / sample_count
                    expected_fraction = mismatches / sample_count
                    if not math.isclose(
                        estimate, expected_estimate, rel_tol=1e-9, abs_tol=1e-9
                    ) or not math.isclose(
                        mismatch_fraction,
                        expected_fraction,
                        rel_tol=1e-12,
                        abs_tol=1e-12,
                    ):
                        raise ValueError
                    if estimate > threshold and status != "FAIL":
                        failures.append(
                            f"{expected_name} passes its STL geometry threshold"
                        )
                except (KeyError, TypeError, ValueError, OverflowError):
                    failures.append(
                        f"{expected_name} has inconsistent STL geometry evidence"
                    )
            if type(size) is not int or size < 0:
                failures.append(f"{expected_name} has an invalid byte count")
                continue
            if digest is None and size == 0:
                if expected_name in artifacts:
                    failures.append(
                        f"{expected_name} is listed but recorded as missing"
                    )
                continue
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
                or size == 0
            ):
                failures.append(f"{expected_name} has an invalid size or SHA-256")
                continue
            inventory = artifacts.get(expected_name)
            if not isinstance(inventory, dict) or inventory != {
                "sha256": digest,
                "size_bytes": size,
            }:
                failures.append(
                    f"{expected_name} disagrees with the artifact inventory"
                )
        expected_check_status = "PASS" if statuses == ["PASS", "PASS"] else "FAIL"
        if check.get("status") != expected_check_status:
            failures.append(f"{subject} export summary disagrees with its file checks")

    if outcome == "DIGITAL_CHECKS_PASSED":
        if seen_subjects != {"body", "lid"}:
            failures.append("accepted outcome is missing body or lid export checks")
        required = {"body.step", "body.stl", "lid.step", "lid.stl"}
        if not required.issubset(artifacts):
            failures.append(
                "accepted outcome is missing required export inventory entries"
            )
    profile = report.get("acceptance_profile")
    snapshot_policy = None
    if profile is not None:
        if not isinstance(profile, dict):
            failures.append("acceptance profile record is invalid")
        else:
            profile_path = profile.get("path")
            profile_path_id = None
            if isinstance(profile_path, str):
                profile_path_id = Path(profile_path).stem
            if profile_path_id != profile.get("identifier"):
                failures.append("acceptance profile identity does not match its path")
            profile_inventory = artifacts.get("acceptance-profile.json")
            profile_digest = profile.get("sha256")
            if (
                not isinstance(profile_inventory, dict)
                or profile_inventory.get("sha256") != profile_digest
            ):
                failures.append(
                    "acceptance profile hash disagrees with package inventory"
                )
            try:
                snapshot_path = folder / "acceptance-profile.json"
                if snapshot_path.is_symlink():
                    raise ValueError("profile snapshot must not be a symlink")
                snapshot_hash = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
                snapshot_policy = load_policy(snapshot_path)
                if snapshot_hash != profile_digest:
                    failures.append("acceptance profile snapshot hash does not match")
                if snapshot_policy != profile.get("policy"):
                    failures.append("acceptance profile rules disagree with snapshot")
            except (OSError, ValueError, json.JSONDecodeError) as error:
                failures.append(f"acceptance profile snapshot is invalid: {error}")

            profile_checks = [
                check
                for check in checks
                if isinstance(check, dict) and check.get("code") == "acceptance_profile"
            ]
            envelope_policy = (
                snapshot_policy.get("maximum_enclosure_envelope_mm")
                if snapshot_policy
                else None
            )
            envelope_checks = [
                check
                for check in checks
                if isinstance(check, dict)
                and check.get("code") == "maximum_enclosure_envelope"
            ]
            if envelope_policy is None:
                if envelope_checks:
                    failures.append(
                        "maximum enclosure envelope check has no profile limit"
                    )
            elif len(envelope_checks) != 1:
                failures.append(
                    "profile must contain exactly one maximum enclosure envelope check"
                )
            else:
                dimensions = report.get("dimensions_mm", {}).get("assembled")
                if not isinstance(dimensions, dict) or not {"x", "y", "z"}.issubset(
                    dimensions
                ):
                    failures.append(
                        "maximum enclosure envelope has no assembled dimensions"
                    )
                elif any(
                    isinstance(dimensions[axis], bool)
                    or not isinstance(dimensions[axis], (int, float))
                    or not math.isfinite(dimensions[axis])
                    for axis in ("x", "y", "z")
                ):
                    failures.append(
                        "maximum enclosure envelope has invalid assembled dimensions"
                    )
                else:
                    expected_envelope_check = _maximum_enclosure_envelope_check(
                        dimensions, envelope_policy
                    )
                    for key, expected in expected_envelope_check.items():
                        if envelope_checks[0].get(key) != expected:
                            failures.append(
                                "maximum enclosure envelope check contradicts "
                                f"its dimensions or profile limit ({key})"
                            )
            if len(profile_checks) != 1:
                failures.append(
                    "report must contain exactly one acceptance profile check"
                )
            else:
                profile_check = profile_checks[0]
                policy = profile.get("policy")
                if not isinstance(policy, dict) or snapshot_policy is None:
                    failures.append("acceptance profile policy is missing")
                else:
                    evaluation_checks = [
                        check
                        for check in checks
                        if isinstance(check, dict)
                        and check.get("code") != "acceptance_profile"
                    ]
                    expected_profile = evaluate_policy(
                        {
                            "checks": evaluation_checks,
                            "evaluated_status": (
                                "FAIL"
                                if any(
                                    check.get("status") == "FAIL"
                                    for check in evaluation_checks
                                )
                                else "PASS"
                            ),
                            "warning_count": 0,
                        },
                        snapshot_policy,
                    )
                    profile_id = profile.get("identifier")
                    if profile_check.get("profile") != profile_id:
                        failures.append(
                            "acceptance profile check has a different profile id"
                        )
                    if profile_check.get("required_checks") != policy.get(
                        "required_checks"
                    ):
                        failures.append(
                            "acceptance profile check lists different requirements"
                        )
                    if (
                        profile.get("status") != expected_profile["status"]
                        or profile.get("reasons") != expected_profile["reasons"]
                        or profile_check.get("status") != expected_profile["status"]
                        or profile_check.get("reasons") != expected_profile["reasons"]
                    ):
                        failures.append(
                            "acceptance profile result contradicts its checks"
                        )
                    if (
                        outcome == "DIGITAL_CHECKS_PASSED"
                        and expected_profile["status"] != "PASS"
                    ):
                        failures.append("accepted outcome does not satisfy its profile")
    return failures


def verify_acceptance(folder, *, expected_report_sha256=None):
    """Verify package consistency and optionally pin report bytes by trusted hash."""
    folder = Path(folder)
    report_path = folder / "report.json"
    if report_path.is_symlink():
        raise ValueError("Report must not be a symlink")
    report_bytes = report_path.read_bytes()
    report_sha256 = hashlib.sha256(report_bytes).hexdigest()
    if expected_report_sha256 is not None:
        if (
            not isinstance(expected_report_sha256, str)
            or len(expected_report_sha256) != 64
            or any(
                character not in "0123456789abcdefABCDEF"
                for character in expected_report_sha256
            )
        ):
            raise ValueError("Trusted report SHA-256 must be 64 hexadecimal characters")
        expected_report_sha256 = expected_report_sha256.lower()
    report = json.loads(report_bytes)
    if report.get("schema_version") != "1.0":
        raise ValueError("Unsupported acceptance schema")
    artifacts = report.get("artifacts", {})
    if (
        not isinstance(artifacts, dict)
        or "design.json" not in artifacts
        or "report.md" not in artifacts
    ):
        raise ValueError("Incomplete artifact bindings")
    if report.get("digital_status") not in {
        "DIGITAL_CHECKS_PASSED",
        "REVISION_REQUIRED",
    }:
        raise ValueError("Invalid digital status")
    integrity_failures = []
    for name, expected in artifacts.items():
        if (
            Path(name).name != name
            or name in {".", "..", "report.json"}
            or "\\" in name
        ):
            raise ValueError("Invalid artifact filename")
        try:
            if fingerprint(folder / name) != expected:
                integrity_failures.append(name)
        except (OSError, ValueError):
            integrity_failures.append(name)
    consistency_failures = _report_consistency_failures(report, artifacts, folder)
    if expected_report_sha256 is None:
        authenticity = "UNVERIFIED"
    elif report_sha256 == expected_report_sha256:
        authenticity = "MATCHED_TRUSTED_SHA256"
    else:
        authenticity = "TRUSTED_SHA256_MISMATCH"
    return {
        "package_integrity": "FAIL" if integrity_failures else "PASS",
        "changed_or_missing": integrity_failures,
        "report_consistency": "FAIL" if consistency_failures else "PASS",
        "inconsistencies": consistency_failures,
        "acceptance_outcome": report["digital_status"],
        "report_sha256": report_sha256,
        "trusted_report_sha256": expected_report_sha256,
        "authenticity": authenticity,
    }


def run_acceptance_verify(arguments):
    parser = argparse.ArgumentParser(prog="zcad accept-verify")
    parser.add_argument("folder", type=Path)
    parser.add_argument(
        "--trusted-report-sha256",
        help="Expected report.json SHA-256 recorded outside this package",
    )
    args = parser.parse_args(arguments)
    result = verify_acceptance(
        args.folder, expected_report_sha256=args.trusted_report_sha256
    )
    print(json.dumps(result, indent=2))
    if (
        result["package_integrity"] != "PASS"
        or result["report_consistency"] != "PASS"
        or result["authenticity"] == "TRUSTED_SHA256_MISMATCH"
    ):
        raise SystemExit(1)


def _changed_measurements(baseline, variant, path=""):
    changes = []
    if isinstance(baseline, dict) and isinstance(variant, dict):
        for key in sorted(baseline.keys() & variant.keys()):
            if key == "exports" or key in {
                "max_dimension_difference_mm",
                "round_trip_tolerance",
                "tolerance",
                "volume_difference_mm3",
            }:
                continue
            child_path = f"{path}.{key}" if path else key
            changes.extend(
                _changed_measurements(baseline[key], variant[key], child_path)
            )
    elif isinstance(baseline, list) and isinstance(variant, list):
        for index, (before, after) in enumerate(zip(baseline, variant, strict=False)):
            changes.extend(_changed_measurements(before, after, f"{path}[{index}]"))
    elif (
        isinstance(baseline, (int, float))
        and not isinstance(baseline, bool)
        and isinstance(variant, (int, float))
        and not isinstance(variant, bool)
        and not math.isclose(baseline, variant, rel_tol=1e-12, abs_tol=1e-12)
    ):
        field = path.rsplit(".", 1)[-1].split("[", 1)[0]
        if any(unit in field for unit in ("_mm", "volume", "area")):
            unit = "mm³" if "mm3" in field or "volume" in field else "mm²"
            if "_mm" in field and "mm2" not in field and "mm3" not in field:
                unit = "mm"
            changes.append(
                {
                    "measurement": path,
                    "baseline": baseline,
                    "variant": variant,
                    "delta": variant - baseline,
                    "unit": unit,
                }
            )
    return changes


def _robustness_measurement_label(path):
    dimension_labels = {0: "source width", 1: "source depth", 2: "source height"}
    if path.startswith("source_dimensions_mm["):
        index = int(path.removeprefix("source_dimensions_mm[").removesuffix("]"))
        return dimension_labels.get(index, path)
    return (
        path.replace("_mm3", "")
        .replace("_mm2", "")
        .replace("_mm", "")
        .replace("_", " ")
    )


def _format_robustness_change(item):
    parts = item["check"].split(":")
    label = (parts[1] or parts[0]) if len(parts) > 2 else parts[0]
    baseline = item["baseline"]
    variant = item["variant"]
    baseline_status = baseline.get("status", "ABSENT") if baseline else "ABSENT"
    variant_status = variant.get("status", "UNKNOWN")
    details = []
    if baseline_status != variant_status:
        details.append(f"status {baseline_status} → {variant_status}")
    details.extend(
        f"{_robustness_measurement_label(measurement['measurement'])} "
        f"{measurement['baseline']:.4f} → "
        f"{measurement['variant']:.4f} {measurement['unit']} "
        f"(Δ {measurement['delta']:+.4f} {measurement['unit']})"
        for measurement in item["changed_measurements"]
    )
    if not details:
        details.append("check evidence changed")
    return f"{label}: " + ", ".join(details)


def build_robustness_report(
    design_path, output, parameter, values, *, profile_path=None
):
    """Compare digital acceptance across explicit variants of one numeric parameter."""
    design_path = Path(design_path)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Robustness output must be an empty directory")

    original = json.loads(design_path.read_text())
    if original.get("type") != "pico2_enclosure_fit":
        raise ValueError("Robustness analysis supports pico2_enclosure_fit only")
    parameters = original.get("parameters", {})
    if parameter not in parameters:
        raise ValueError(f"Unknown design parameter: {parameter}")
    baseline_value = parameters[parameter]
    if isinstance(baseline_value, bool) or not isinstance(baseline_value, (int, float)):
        raise ValueError(f"{parameter} is not a numeric parameter")
    if not math.isfinite(baseline_value):
        raise ValueError(f"{parameter} baseline must be finite")
    if not values:
        raise ValueError("At least one variant value is required")
    requested = [float(value) for value in values]
    if len(requested) > 20:
        raise ValueError("At most 20 variant values may be tested per report")
    if any(not math.isfinite(value) for value in requested):
        raise ValueError("Variant values must be finite numbers")
    if len(set(requested)) != len(requested):
        raise ValueError("Variant values must be unique")

    cases = [float(baseline_value)] + [
        value for value in requested if value != float(baseline_value)
    ]
    rows = []
    with tempfile.TemporaryDirectory(prefix="zcad-robustness-") as temporary:
        root = Path(temporary)
        variant_design = root / "design.json"
        for index, value in enumerate(cases):
            document = json.loads(json.dumps(original))
            document["parameters"][parameter] = value
            variant_design.write_text(json.dumps(document, indent=2) + "\n")
            package = root / f"case-{index:03d}"
            revision = f"robustness-{parameter}-{index:03d}"
            report = build_acceptance(
                variant_design, package, revision, profile_path=profile_path
            )
            check_results = {}
            for check_index, check in enumerate(report["checks"]):
                snapshot = json.loads(json.dumps(check))
                for artifact in snapshot.get("exports", {}).values():
                    artifact.pop("sha256", None)
                    artifact.pop("size_bytes", None)
                key = f"{check['code']}:{check.get('subject', '')}:{check_index:03d}"
                check_results[key] = snapshot
            rows.append(
                {
                    "value": value,
                    "digital_status": report["digital_status"],
                    "profile_status": report["acceptance_profile"]["status"],
                    "checks": check_results,
                }
            )

    baseline_checks = rows[0]["checks"]
    for row in rows:
        row["changed_checks"] = [
            {
                "check": key,
                "baseline": baseline_checks.get(key),
                "variant": value,
                "changed_measurements": _changed_measurements(
                    baseline_checks.get(key, {}), value
                ),
            }
            for key, value in row["checks"].items()
            if baseline_checks.get(key) != value
        ]
    result = {
        "schema_version": "1.0",
        "analysis": "DIGITAL_PARAMETER_VARIATION",
        "scope": (
            "Synthetic CAD parameter variants; no printer or physical tolerance "
            "is modeled."
        ),
        "design": str(design_path.resolve()),
        "design_sha256": hashlib.sha256(design_path.read_bytes()).hexdigest(),
        "parameter": parameter,
        "baseline_value": float(baseline_value),
        "tested_values": cases,
        "cases": rows,
        "interpretation": (
            "Results describe only the declared CAD variants and selected digital "
            "acceptance profile."
        ),
    }
    (output / "robustness.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    lines = [
        "# Digital robustness report",
        "",
        f"Parameter: `{parameter}`; baseline: **{baseline_value:g}**",
        "",
        "This report varies one declared CAD parameter and reruns digital acceptance. "
        "It does not model printer accuracy, material behavior, hardware "
        "variation, or physical fit.",
        "",
        "| Value | Digital outcome | Profile | Changed checks and CAD measurements |",
        "| ---: | --- | --- | --- |",
    ]
    for row in rows:
        changed = (
            "; ".join(_format_robustness_change(item) for item in row["changed_checks"])
            or "None"
        )
        lines.append(
            f"| {row['value']:g} | {row['digital_status']} | "
            f"{row['profile_status']} | {changed} |"
        )
    lines.extend(
        [
            "",
            "The report includes every case's check status and change list in "
            "`robustness.json`.",
        ]
    )
    (output / "report.md").write_text("\n".join(lines) + "\n")
    return result


def run_acceptance_robustness(arguments):
    parser = argparse.ArgumentParser(prog="zcad accept-robustness")
    parser.add_argument("design", type=Path)
    parser.add_argument("parameter")
    parser.add_argument("--values", nargs="+", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args(arguments)
    result = build_robustness_report(
        args.design,
        args.output,
        args.parameter,
        args.values,
        profile_path=args.profile,
    )
    print(json.dumps(result, indent=2))
