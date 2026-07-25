"""Tests for the reusable board-fastening package."""

import importlib


def test_fastening_modules_are_importable() -> None:
    modules = (
        "zcad.fastening",
        "zcad.fastening.artifacts",
        "zcad.fastening.backend",
        "zcad.fastening.none",
        "zcad.fastening.printed_standoff",
        "zcad.fastening.heat_set_insert",
        "zcad.fastening.registry",
        "zcad.fastening.verification",
    )

    for module in modules:
        assert importlib.import_module(module)
