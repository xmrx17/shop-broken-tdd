"""Order checkout.

The rules live in `src/shop/specs/checkout.md` - read it first.
Both functions below are stubs: their signature is final, the bodies are yours.
Do not change the constants: the tests rely on them.
"""

import re

from shop.money import percent_of

PROMO_CODES = {"WELCOME10": 10, "SUMMER15": 15, "VIP35": 35}
SUPPORTED_CITIES = ("msk", "spb")
MAX_DISCOUNT_PERCENT = 30
VAT_PERCENT = 20
SHIPPING_KOPEKS = 49_000
FREE_DELIVERY_FROM_KOPEKS = 500_000
TIER_DISCOUNTS = ((10, 5), (25, 10), (50, 15))
REQUIRED_LINE_KEYS = ("sku", "qty", "unit_price_kopecks")


def _parse_integer(value: str) -> int | None:
    # Match int's decimal syntax without relying on exceptions.
    if re.fullmatch(r"\s*[+-]?\d(?:_?\d)*\s*", value) is None:
        return None
    return int(value)


def _validate_line(line: dict[str, str]) -> str | None:
    if any(key not in line for key in REQUIRED_LINE_KEYS):
        return "Missing required key"
    if not line["sku"]:
        return "Empty SKU"
    quantity = _parse_integer(line["qty"])
    if quantity is None or quantity <= 0:
        return "Quantity must be a positive integer"
    price = _parse_integer(line["unit_price_kopecks"])
    if price is None or price < 0:
        return "Price must be a non-negative integer"
    return None


def validate_order(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> str | None:
    """Return a human readable reason why the order is invalid, or None if it is fine."""
    if not lines:
        return "Order has no lines"
    seen: set[str] = set()
    for number, line in enumerate(lines, start=1):
        reason = _validate_line(line)
        if reason is not None:
            return f"Line {number}: {reason}"
        if line["sku"] in seen:
            return f"Line {number}: Duplicate SKU"
        seen.add(line["sku"])
    if promo_code and promo_code not in PROMO_CODES:
        return "Unknown promo code"
    if shipping_city and shipping_city not in SUPPORTED_CITIES:
        return "Unsupported shipping city"
    return None


def calculate_order_total(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> int | None:
    """Return the order total in kopecks, or None if the order is invalid."""
    if validate_order(lines, promo_code, shipping_city) is not None:
        return None
    subtotal = sum(int(line["qty"]) * int(line["unit_price_kopecks"]) for line in lines)
    quantity = sum(int(line["qty"]) for line in lines)
    tier_percent = 0
    for threshold, percent in TIER_DISCOUNTS:
        if quantity >= threshold:
            tier_percent = percent
    discount_percent = min(MAX_DISCOUNT_PERCENT, max(tier_percent, PROMO_CODES.get(promo_code, 0)))
    discounted_subtotal = subtotal - percent_of(subtotal, discount_percent)
    shipping = 0
    if shipping_city and discounted_subtotal < FREE_DELIVERY_FROM_KOPEKS:
        shipping = SHIPPING_KOPEKS
    base = discounted_subtotal + shipping
    return base + percent_of(base, VAT_PERCENT)
