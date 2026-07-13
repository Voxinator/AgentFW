"""Order validator.

Validates order records against the rules in schema/fixture-schema.json.
Stdlib only; the schema's structural rules are implemented directly here
so the package has no runtime dependency on a JSON Schema library.
"""

import re

ORDER_ID_RE = re.compile(r"^ORD-[0-9]{4}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SKU_RE = re.compile(r"^SKU-[A-Z0-9]{5}$")
STATUSES = ("pending", "paid", "shipped", "cancelled")
CURRENCIES = ("USD", "EUR", "GBP")

REQUIRED_FIELDS = ("order_id", "customer", "status", "currency", "items", "total_cents")
REQUIRED_ITEM_FIELDS = ("sku", "quantity", "unit_price_cents")


def validate_order(order):
    """Validate a single order dict.

    Returns a list of error strings; an empty list means the order is valid.
    Each error starts with a stable machine-readable code.
    """
    errors = []
    if not isinstance(order, dict):
        return ["not_an_object: order must be a JSON object"]

    for field in REQUIRED_FIELDS:
        if field not in order:
            errors.append("missing_field: %s" % field)
    if errors:
        return errors

    if not isinstance(order["order_id"], str) or not ORDER_ID_RE.match(order["order_id"]):
        errors.append("bad_order_id: %r" % (order["order_id"],))

    customer = order["customer"]
    if not isinstance(customer, dict):
        errors.append("bad_customer: customer must be an object")
    else:
        if not isinstance(customer.get("name"), str) or not customer.get("name"):
            errors.append("missing_field: customer.name")
        email = customer.get("email")
        if not isinstance(email, str):
            errors.append("missing_field: customer.email")
        elif not EMAIL_RE.match(email):
            errors.append("bad_email: %r" % (email,))

    if order["status"] not in STATUSES:
        errors.append("bad_status: %r" % (order["status"],))

    if order["currency"] not in CURRENCIES:
        errors.append("bad_currency: %r" % (order["currency"],))

    items = order["items"]
    if not isinstance(items, list) or not items:
        errors.append("bad_items: items must be a non-empty array")
        items = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append("bad_item: items[%d] must be an object" % i)
            continue
        for field in REQUIRED_ITEM_FIELDS:
            if field not in item:
                errors.append("missing_field: items[%d].%s" % (i, field))
        sku = item.get("sku")
        if isinstance(sku, str) and not SKU_RE.match(sku):
            errors.append("bad_sku: items[%d] %r" % (i, sku))
        for field in ("quantity", "unit_price_cents"):
            value = item.get(field)
            if field in item and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
                errors.append("bad_%s: items[%d] %r" % (field, i, value))

    if not errors:
        expected = compute_total_cents(order)
        if order["total_cents"] != expected:
            errors.append(
                "total_mismatch: total_cents=%d expected=%d" % (order["total_cents"], expected)
            )

    return errors


def compute_total_cents(order):
    """Sum of quantity * unit_price_cents over all items."""
    return sum(item["quantity"] * item["unit_price_cents"] for item in order["items"])


def is_valid(order):
    return not validate_order(order)
