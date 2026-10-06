"""Declarative design inputs."""

from zcad.designs.board_display import (
    BoardDisplayDesign,
    build_board_display_design,
    load_board_display_design,
    parse_board_display_design,
    parse_display_spec,
    resolve_board_display_design_product,
)

__all__ = [
    "BoardDisplayDesign",
    "build_board_display_design",
    "load_board_display_design",
    "parse_board_display_design",
    "parse_display_spec",
    "resolve_board_display_design_product",
]
