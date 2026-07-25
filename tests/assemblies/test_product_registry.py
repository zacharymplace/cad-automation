"""Tests for the board-display product registry."""

from dataclasses import replace

import pytest

from zcad.assemblies import (
    get_board_display_product,
    list_board_display_products,
)
from zcad.assemblies.pico2_oled import PICO2_OLED_PRODUCT
from zcad.assemblies.product_registry import _build_product_registry
from zcad.assemblies.xiao_esp32s3_oled import (
    XIAO_ESP32S3_OLED_PRODUCT,
)


def test_registry_lists_registered_products() -> None:
    products = list_board_display_products()

    assert products == (
        PICO2_OLED_PRODUCT,
        XIAO_ESP32S3_OLED_PRODUCT,
    )


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        ("PICO2_OLED", PICO2_OLED_PRODUCT),
        ("XIAO_ESP32S3_OLED", XIAO_ESP32S3_OLED_PRODUCT),
    ],
)
def test_registry_resolves_product_by_identifier(
    identifier: str,
    expected: object,
) -> None:
    assert get_board_display_product(identifier) is expected


def test_registry_rejects_empty_lookup_identifier() -> None:
    with pytest.raises(
        ValueError,
        match="identifier must not be empty",
    ):
        get_board_display_product("")


def test_registry_rejects_unknown_identifier() -> None:
    with pytest.raises(
        KeyError,
        match="unknown board-display product identifier",
    ):
        get_board_display_product("UNKNOWN_PRODUCT")


def test_registry_rejects_duplicate_identifiers() -> None:
    duplicate = replace(
        XIAO_ESP32S3_OLED_PRODUCT,
        identifier=PICO2_OLED_PRODUCT.identifier,
    )

    with pytest.raises(
        ValueError,
        match="duplicate board-display product identifier",
    ):
        _build_product_registry(
            (
                PICO2_OLED_PRODUCT,
                duplicate,
            )
        )


def test_registry_result_is_immutable_snapshot() -> None:
    products = list_board_display_products()

    assert isinstance(products, tuple)
