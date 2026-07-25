"""Registry for declarative board-display products."""

from collections.abc import Iterable

from zcad.assemblies.board_display import BoardDisplayProduct
from zcad.assemblies.pico2_oled import PICO2_OLED_PRODUCT
from zcad.assemblies.xiao_esp32s3_oled import (
    XIAO_ESP32S3_OLED_PRODUCT,
)


def _build_product_registry(
    products: Iterable[BoardDisplayProduct],
) -> dict[str, BoardDisplayProduct]:
    """Build a validated product registry keyed by identifier."""
    registry: dict[str, BoardDisplayProduct] = {}

    for product in products:
        product.validate()

        if product.identifier in registry:
            raise ValueError(
                f"duplicate board-display product identifier: {product.identifier}"
            )

        registry[product.identifier] = product

    return registry


_BOARD_DISPLAY_PRODUCTS = _build_product_registry(
    (
        PICO2_OLED_PRODUCT,
        XIAO_ESP32S3_OLED_PRODUCT,
    )
)


def list_board_display_products() -> tuple[BoardDisplayProduct, ...]:
    """Return all registered board-display products."""
    return tuple(_BOARD_DISPLAY_PRODUCTS.values())


def get_board_display_product(
    identifier: str,
) -> BoardDisplayProduct:
    """Return a registered board-display product by identifier."""
    if not identifier.strip():
        raise ValueError("identifier must not be empty")

    try:
        return _BOARD_DISPLAY_PRODUCTS[identifier]
    except KeyError as error:
        raise KeyError(
            f"unknown board-display product identifier: {identifier}"
        ) from error
