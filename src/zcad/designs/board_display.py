"""JSON design input for registered board-display products."""

import json
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any

from zcad_core.assemblies import DeviceAssembly

from zcad.assemblies.board_display import (
    BoardDisplayAssemblyParameters,
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

    product = get_board_display_product(design.product)

    return build_board_display_product(
        product,
        parameters=design.parameters,
    )
