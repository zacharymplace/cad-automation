"""JSON design input for registered board-display products."""

import json
import math
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any

from zcad_core.assemblies import DeviceAssembly
from zcad_core.hardware.electronics import DisplaySpec

from zcad.assemblies.board_display import (
    BoardDisplayAssemblyParameters,
    BoardDisplayProduct,
    build_board_display_product,
)
from zcad.assemblies.product_registry import (
    get_board_display_product,
)

_SCHEMA_VERSION = "1"
_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "product",
        "parameters",
        "display",
    }
)
_PARAMETER_FIELDS = frozenset(
    field.name for field in fields(BoardDisplayAssemblyParameters)
)


@dataclass(frozen=True)
class BoardDisplayDesign:
    """Validated input selecting a registered board-display product."""

    schema_version: str
    product: str
    parameters: BoardDisplayAssemblyParameters
    display: DisplaySpec | None = None


def _require_object(
    value: object,
    *,
    context: str,
) -> dict[str, Any]:
    """Return a JSON object or raise a contextual validation error."""
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a JSON object")

    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{context} keys must be strings")

    return value


def _reject_unknown_fields(
    values: dict[str, Any],
    *,
    allowed: frozenset[str],
    context: str,
) -> None:
    """Reject fields that are not part of the design contract."""
    unknown = sorted(set(values) - allowed)

    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"unknown {context} field(s): {joined}")


def _parse_parameter_values(
    values: dict[str, Any],
) -> dict[str, float]:
    """Parse validated numeric board-display parameter overrides."""
    _reject_unknown_fields(
        values,
        allowed=_PARAMETER_FIELDS,
        context="parameter",
    )

    parsed: dict[str, float] = {}

    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise ValueError(f"parameter {name} must be a number")

        parsed[name] = float(value)

    return parsed


def parse_display_spec(document: object) -> DisplaySpec:
    """Accept explicit mechanical data with its source, never implicit provenance."""
    values = _require_object(document, context="display")
    allowed = frozenset(field.name for field in fields(DisplaySpec))
    _reject_unknown_fields(values, allowed=allowed, context="display")
    text_fields = {
        "identifier",
        "mount_style",
        "geometry_evidence_status",
        "geometry_source",
    }
    required = {
        "identifier",
        "module_width_mm",
        "module_height_mm",
        "module_depth_mm",
        "active_width_mm",
        "active_height_mm",
        "geometry_source",
    }
    missing = sorted(required - values.keys())
    if missing:
        raise ValueError(f"missing display field(s): {', '.join(missing)}")
    nullable = {
        "mounting_hole_diameter_mm",
        "mounting_hole_spacing_x_mm",
        "mounting_hole_spacing_y_mm",
        "pcb_thickness_mm",
        "panel_width_mm",
        "panel_height_mm",
        "panel_thickness_mm",
    }
    for name, value in values.items():
        if name in text_fields:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"display {name} must be a nonempty string")
        elif value is not None:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"display {name} must be a finite number")
        elif name not in nullable:
            raise ValueError(f"display {name} must be a finite number")
    display = DisplaySpec(**values)
    if display.mount_style not in {"adhesive", "bezel", "screws", "snap"}:
        raise ValueError("invalid display mount_style")
    display.validate()
    if (
        abs(display.active_center_x_mm) + display.active_width_mm / 2
        > display.module_width_mm / 2
        or abs(display.active_center_y_mm) + display.active_height_mm / 2
        > display.module_height_mm / 2
    ):
        raise ValueError("display active area must lie within the module outline")
    return display


def resolve_board_display_design_product(
    design: BoardDisplayDesign,
) -> BoardDisplayProduct:
    """Resolve hardware consistently for building, inspection, and analysis."""
    product = get_board_display_product(design.product)
    if design.display is not None:
        display = parse_display_spec(
            {
                field.name: getattr(design.display, field.name)
                for field in fields(DisplaySpec)
            }
        )
        product = replace(product, display=display)
    return product


def parse_board_display_design(
    document: object,
) -> BoardDisplayDesign:
    """Parse and validate a board-display JSON document."""
    root = _require_object(
        document,
        context="design",
    )

    _reject_unknown_fields(
        root,
        allowed=_TOP_LEVEL_FIELDS,
        context="design",
    )

    schema_version = root.get("schema_version")

    if schema_version != _SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {_SCHEMA_VERSION!r}")

    product_identifier = root.get("product")

    if not isinstance(product_identifier, str):
        raise ValueError("product must be a string")

    if not product_identifier.strip():
        raise ValueError("product must not be empty")

    product = get_board_display_product(product_identifier)

    raw_parameters = root.get("parameters", {})
    parameter_object = _require_object(
        raw_parameters,
        context="parameters",
    )
    overrides = _parse_parameter_values(parameter_object)

    parameters = replace(
        product.default_parameters,
        **overrides,
    )
    parameters.validate()

    return BoardDisplayDesign(
        schema_version=_SCHEMA_VERSION,
        product=product.identifier,
        parameters=parameters,
        display=parse_display_spec(root["display"]) if "display" in root else None,
    )


def load_board_display_design(
    path: str | Path,
) -> BoardDisplayDesign:
    """Load and validate a board-display design from JSON."""
    resolved = Path(path)

    try:
        document = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON design: {resolved}") from error

    return parse_board_display_design(document)


def build_board_display_design(
    design: BoardDisplayDesign,
) -> DeviceAssembly:
    """Build an assembly from a validated design."""
    if design.schema_version != _SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {_SCHEMA_VERSION!r}")

    product = resolve_board_display_design_product(design)

    return build_board_display_product(
        product,
        parameters=design.parameters,
    )
