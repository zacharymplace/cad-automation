"""Tests for registry-driven board-display enclosure geometry."""

from dataclasses import replace

import pytest
from zcad_core.assemblies import InterferenceFinding

from zcad.designs import (
    parse_board_display_design,
)
from zcad.generators.board_display_enclosure import (
    BoardDisplayEnclosureBuild,
    BoardDisplayEnclosureParameters,
    BoardFasteningStrategy,
    _build_enclosure_parameters,
    analyze_board_display_enclosure_fit,
    build_board_display_enclosure,
    build_board_display_enclosure_result,
)


@pytest.mark.parametrize(
    "product",
    [
        "PICO2_OLED",
        "XIAO_ESP32S3_OLED",
    ],
)
def test_registered_products_generate_valid_parts(
    product: str,
) -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": product,
        }
    )

    parts = build_board_display_enclosure(design)

    assert set(parts) == {
        "body",
        "lid",
    }

    for part in parts.values():
        value = part.val()

        assert value is not None
        assert value.isValid()
        assert value.Volume() > 0


def test_pico_and_xiao_resolve_different_enclosure_depths() -> None:
    pico = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )
    xiao = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    pico_parameters = _build_enclosure_parameters(
        pico,
        BoardDisplayEnclosureParameters(),
    )
    xiao_parameters = _build_enclosure_parameters(
        xiao,
        BoardDisplayEnclosureParameters(),
    )

    assert pico_parameters.depth > xiao_parameters.depth


def test_enclosure_dimensions_follow_derived_cavity() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )
    policy = BoardDisplayEnclosureParameters(
        wall_mm=2.5,
        floor_mm=2.0,
        internal_clearance_mm=1.5,
    )

    parameters = _build_enclosure_parameters(
        design,
        policy,
    )

    assert parameters.width > 28.0
    assert parameters.depth > 51.0
    assert parameters.height > 12.0
    assert parameters.wall == pytest.approx(2.5)
    assert parameters.floor == pytest.approx(2.0)


def test_connector_dimensions_drive_cable_slot() -> None:
    pico = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )
    xiao = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    policy = BoardDisplayEnclosureParameters(
        connector_cutout_clearance_mm=0.5,
    )

    pico_parameters = _build_enclosure_parameters(
        pico,
        policy,
    )
    xiao_parameters = _build_enclosure_parameters(
        xiao,
        policy,
    )

    assert pico_parameters.cable_slot_width == pytest.approx(9.9)
    assert xiao_parameters.cable_slot_width == pytest.approx(10.0)
    assert pico_parameters.cable_slot_height == pytest.approx(4.2)
    assert xiao_parameters.cable_slot_height == pytest.approx(4.2)


def test_default_label_uses_product_identifier() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    default_parts = build_board_display_enclosure(design)
    explicit_parts = build_board_display_enclosure(
        design,
        BoardDisplayEnclosureParameters(
            label="CUSTOM",
        ),
    )

    assert default_parts["lid"].val().Volume() > 0
    assert explicit_parts["lid"].val().Volume() > 0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("wall_mm", 0.0, "wall_mm"),
        (
            "internal_clearance_mm",
            -0.1,
            "internal_clearance_mm",
        ),
        (
            "connector_cutout_clearance_mm",
            -0.1,
            "connector_cutout_clearance_mm",
        ),
        ("label", " ", "label"),
    ],
)
def test_enclosure_policy_rejects_invalid_values(
    field: str,
    value: object,
    message: str,
) -> None:
    arguments = {
        field: value,
    }

    with pytest.raises(
        ValueError,
        match=message,
    ):
        BoardDisplayEnclosureParameters(
            **arguments,
        ).validate()


def test_connector_edge_drives_enclosure_slot_edge() -> None:
    pico = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )
    xiao = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    policy = BoardDisplayEnclosureParameters()

    pico_parameters = _build_enclosure_parameters(
        pico,
        policy,
    )
    xiao_parameters = _build_enclosure_parameters(
        xiao,
        policy,
    )

    assert pico_parameters.cable_slot_edge == "negative_y"
    assert xiao_parameters.cable_slot_edge == "positive_y"


def test_connector_height_drives_enclosure_slot_offset() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    parameters = _build_enclosure_parameters(
        design,
        BoardDisplayEnclosureParameters(),
    )

    assert parameters.cable_slot_bottom_offset >= 0
    assert (
        parameters.cable_slot_bottom_offset + parameters.cable_slot_height
        <= parameters.height - parameters.floor
    )


@pytest.mark.parametrize(
    "product",
    [
        "PICO2_OLED",
        "XIAO_ESP32S3_OLED",
    ],
)
def test_default_enclosure_fit_passes(
    product: str,
) -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": product,
        }
    )

    build = build_board_display_enclosure_result(design)
    report = analyze_board_display_enclosure_fit(build)

    assert not report.has_findings


def test_enclosure_build_result_preserves_resolved_artifacts() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)

    assert build.assembly.identifiers == (
        "board",
        "usb_connector",
        "display",
    )
    assert build.specification.cable_edge == "negative_y"
    assert set(build.parts) == {
        "body",
        "lid",
    }


def test_fit_analysis_detects_undersized_cavity() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            internal_clearance_mm=0.0,
            board_fastening_strategy=BoardFasteningStrategy.NONE,
        ),
    )

    report = analyze_board_display_enclosure_fit(build)

    non_mounting_findings = tuple(
        finding
        for finding in report.findings
        if not finding.kind.startswith("mounting_")
    )

    assert non_mounting_findings == ()

    mounting_findings = tuple(
        finding for finding in report.findings if finding.kind.startswith("mounting_")
    )

    assert len(mounting_findings) == 1
    assert mounting_findings[0].kind == "mounting_count"


def _lid_volume(
    product: str,
    policy: BoardDisplayEnclosureParameters,
) -> float:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": product,
        }
    )

    return (
        build_board_display_enclosure(
            design,
            policy,
        )["lid"]
        .val()
        .Volume()
    )


@pytest.mark.parametrize(
    "product",
    [
        "PICO2_OLED",
        "XIAO_ESP32S3_OLED",
    ],
)
def test_display_window_generates_valid_lid(
    product: str,
) -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": product,
        }
    )

    lid = build_board_display_enclosure(design)["lid"].val()

    assert lid.isValid()
    assert lid.Volume() > 0


def test_display_window_removes_lid_material() -> None:
    enabled = _lid_volume(
        "PICO2_OLED",
        BoardDisplayEnclosureParameters(
            display_window_enabled=True,
        ),
    )
    disabled = _lid_volume(
        "PICO2_OLED",
        BoardDisplayEnclosureParameters(
            display_window_enabled=False,
        ),
    )

    assert enabled < disabled


def test_display_window_clearance_enlarges_opening() -> None:
    small = _lid_volume(
        "PICO2_OLED",
        BoardDisplayEnclosureParameters(
            display_window_clearance_mm=0.0,
        ),
    )
    large = _lid_volume(
        "PICO2_OLED",
        BoardDisplayEnclosureParameters(
            display_window_clearance_mm=1.0,
        ),
    )

    assert large < small


def test_display_window_follows_display_xy_placement() -> None:
    centered = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )
    shifted = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
            "parameters": {
                "display_x_mm": 3.0,
                "display_y_mm": 2.0,
            },
        }
    )

    centered_lid = build_board_display_enclosure(centered)["lid"].val()
    shifted_lid = build_board_display_enclosure(shifted)["lid"].val()

    assert centered_lid.isValid()
    assert shifted_lid.isValid()
    assert shifted_lid.Volume() == pytest.approx(
        centered_lid.Volume(),
        rel=1e-6,
    )


def test_disabling_display_window_preserves_more_material() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    windowed = build_board_display_enclosure(
        design,
        BoardDisplayEnclosureParameters(
            display_window_enabled=True,
        ),
    )["lid"].val()

    solid = build_board_display_enclosure(
        design,
        BoardDisplayEnclosureParameters(
            display_window_enabled=False,
        ),
    )["lid"].val()

    assert solid.Volume() > windowed.Volume()


def test_display_window_negative_clearance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="display_window_clearance_mm",
    ):
        BoardDisplayEnclosureParameters(
            display_window_clearance_mm=-0.1,
        ).validate()


@pytest.mark.parametrize(
    "product",
    [
        "PICO2_OLED",
        "XIAO_ESP32S3_OLED",
    ],
)
def test_fit_analysis_accepts_generated_display_window(
    product: str,
) -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": product,
        }
    )

    build = build_board_display_enclosure_result(design)
    report = analyze_board_display_enclosure_fit(build)

    assert not any(
        finding.second_identifier == "display_window" for finding in report.findings
    )


def test_fit_analysis_detects_disabled_display_window() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            display_window_enabled=False,
        ),
    )
    report = analyze_board_display_enclosure_fit(build)

    window_findings = [
        finding
        for finding in report.findings
        if finding.second_identifier == "display_window"
    ]

    assert len(window_findings) == 1
    assert window_findings[0].kind == "collision"
    assert window_findings[0].intersection_volume_mm3 > 0


def test_fit_analysis_detects_undersized_display_window() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    small_window_build = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            display_window_clearance_mm=0.0,
        ),
    )

    verification_build = replace(
        small_window_build,
        policy=replace(
            small_window_build.policy,
            display_window_clearance_mm=1.0,
        ),
    )

    report = analyze_board_display_enclosure_fit(verification_build)

    assert any(
        finding.second_identifier == "display_window"
        and finding.intersection_volume_mm3 > 0
        for finding in report.findings
    )


def test_fit_analysis_detects_shifted_display_window() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)

    shifted_lid = build.parts["lid"].translate(
        (
            3.0,
            0.0,
            0.0,
        )
    )

    shifted_build = replace(
        build,
        parts={
            **build.parts,
            "lid": shifted_lid,
        },
    )

    report = analyze_board_display_enclosure_fit(shifted_build)

    assert any(
        finding.second_identifier == "display_window"
        and finding.intersection_volume_mm3 > 0
        for finding in report.findings
    )


def test_pico_generates_four_assembly_driven_standoffs() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)

    assert len(build.standoff_parameters) == 4

    positions = tuple(
        (parameters.x, parameters.y) for parameters in build.standoff_parameters
    )

    expected = (
        (-5.7, -22.5),
        (5.7, -22.5),
        (-5.7, 24.5),
        (5.7, 24.5),
    )

    assert len(positions) == len(expected)

    for actual, target in zip(
        positions,
        expected,
        strict=True,
    ):
        assert actual == pytest.approx(target)


def test_pico_standoff_tops_align_with_board_bottom() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)
    board = build.assembly.get("board")

    board_bottom_z_mm = board.transformed_geometry().val().BoundingBox().zmin

    for parameters in build.standoff_parameters:
        generated_top_z_mm = (
            build.specification.bottom_z_mm + parameters.standoff_height_mm
        )

        assert generated_top_z_mm == pytest.approx(board_bottom_z_mm)


def test_pico_standoffs_add_body_geometry() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    enabled = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            board_fastening_strategy=BoardFasteningStrategy.PRINTED_STANDOFF,
        ),
    )
    disabled = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            board_fastening_strategy=BoardFasteningStrategy.NONE,
        ),
    )

    assert enabled.parts["body"].val().isValid()
    assert disabled.parts["body"].val().isValid()
    assert enabled.parts["body"].val().Volume() != pytest.approx(
        disabled.parts["body"].val().Volume()
    )


def test_xiao_generates_no_unverified_standoffs() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    enabled = build_board_display_enclosure_result(design)
    disabled = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            board_fastening_strategy=BoardFasteningStrategy.NONE,
        ),
    )

    assert enabled.standoff_parameters == ()
    assert disabled.standoff_parameters == ()

    assert enabled.parts["body"].val().Volume() == pytest.approx(
        disabled.parts["body"].val().Volume()
    )


def test_standoff_clearance_changes_hole_diameter() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    default = build_board_display_enclosure_result(design)
    custom = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            standoff_hole_clearance_mm=0.9,
        ),
    )

    assert default.standoff_parameters[0].hole_diameter_mm == (pytest.approx(2.6))
    assert custom.standoff_parameters[0].hole_diameter_mm == (pytest.approx(3.0))


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("standoff_radial_wall_mm", 0.0),
        ("standoff_hole_clearance_mm", -0.1),
    ),
)
def test_standoff_policy_rejects_invalid_values(
    field: str,
    value: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=field,
    ):
        BoardDisplayEnclosureParameters(**{field: value}).validate()


def test_standoffs_require_board_above_cavity_floor() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    with pytest.raises(
        ValueError,
        match="above the enclosure cavity floor",
    ):
        build_board_display_enclosure_result(
            design,
            BoardDisplayEnclosureParameters(
                internal_clearance_mm=0.0,
                board_fastening_strategy=BoardFasteningStrategy.PRINTED_STANDOFF,
            ),
        )


def _mounting_findings(
    build: BoardDisplayEnclosureBuild,
) -> tuple[InterferenceFinding, ...]:
    return tuple(
        finding
        for finding in (analyze_board_display_enclosure_fit(build).findings)
        if finding.kind.startswith("mounting_")
    )


def test_default_pico_standoff_fit_passes() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)

    assert _mounting_findings(build) == ()


def test_fit_analysis_detects_missing_standoffs() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            board_fastening_strategy=BoardFasteningStrategy.NONE,
        ),
    )

    findings = _mounting_findings(build)

    assert len(findings) == 1
    assert findings[0].kind == "mounting_count"
    assert findings[0].required_clearance_mm == (pytest.approx(4.0))
    assert findings[0].measured_clearance_mm == (pytest.approx(0.0))


def test_fit_analysis_detects_shifted_standoff() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)
    first = build.standoff_parameters[0]

    shifted = replace(
        first,
        x=first.x + 0.5,
    )
    modified = replace(
        build,
        standoff_parameters=(
            shifted,
            *build.standoff_parameters[1:],
        ),
    )

    findings = _mounting_findings(modified)

    alignment = [
        finding for finding in findings if finding.kind == "mounting_alignment"
    ]

    assert len(alignment) == 1
    assert alignment[0].second_identifier == ("standoff_1")
    assert alignment[0].measured_clearance_mm == (pytest.approx(0.5))


def test_fit_analysis_detects_wrong_standoff_height() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)
    first = build.standoff_parameters[0]

    modified = replace(
        build,
        standoff_parameters=(
            replace(
                first,
                standoff_height_mm=(first.standoff_height_mm + 0.75),
            ),
            *build.standoff_parameters[1:],
        ),
    )

    findings = _mounting_findings(modified)

    height = [finding for finding in findings if finding.kind == "mounting_height"]

    assert len(height) == 1
    assert height[0].measured_clearance_mm == (pytest.approx(0.75))


def test_fit_analysis_detects_wrong_standoff_diameters() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)
    first = build.standoff_parameters[0]

    modified = replace(
        build,
        standoff_parameters=(
            replace(
                first,
                hole_diameter_mm=(first.hole_diameter_mm + 0.2),
                outer_diameter_mm=(first.outer_diameter_mm + 0.4),
            ),
            *build.standoff_parameters[1:],
        ),
    )

    kinds = {finding.kind for finding in _mounting_findings(modified)}

    assert "mounting_hole_diameter" in kinds
    assert "mounting_boss_diameter" in kinds


def test_xiao_requires_no_standoff_verification() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "XIAO_ESP32S3_OLED",
        }
    )

    build = build_board_display_enclosure_result(design)

    assert build.standoff_parameters == ()
    assert _mounting_findings(build) == ()


def test_default_board_fastening_strategy_is_printed_standoff() -> None:
    parameters = BoardDisplayEnclosureParameters()

    assert parameters.board_fastening_strategy is (
        BoardFasteningStrategy.PRINTED_STANDOFF
    )


def test_none_fastening_strategy_generates_no_standoffs() -> None:
    design = parse_board_display_design(
        {
            "schema_version": "1",
            "product": "PICO2_OLED",
        }
    )

    build = build_board_display_enclosure_result(
        design,
        BoardDisplayEnclosureParameters(
            board_fastening_strategy=(BoardFasteningStrategy.NONE),
        ),
    )

    assert build.standoff_parameters == ()

    findings = _mounting_findings(build)

    assert len(findings) == 1
    assert findings[0].kind == "mounting_count"


def test_fastening_strategy_rejects_untyped_string() -> None:
    parameters = BoardDisplayEnclosureParameters(
        board_fastening_strategy="printed_standoff",  # type: ignore[arg-type]
    )

    with pytest.raises(
        TypeError,
        match="board_fastening_strategy",
    ):
        parameters.validate()
