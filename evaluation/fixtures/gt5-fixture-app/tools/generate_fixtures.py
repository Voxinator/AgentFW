#!/usr/bin/env python3
"""Regenerate all JSON test fixtures from schema/fixture-schema.json.

Deterministic by construction: every value is derived arithmetically from
the case index and the schema's fixture manifest (no clocks, no uuids, no
unseeded randomness), and files are written with sorted keys and a trailing
newline. Running this script twice always produces byte-identical output.

Usage:
    python3 tools/generate_fixtures.py [output_dir]

Default output_dir is tests/fixtures/ relative to the project root.
"""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "schema", "fixture-schema.json")

CUSTOMER_NAMES = [
    "Ada Lovelace",
    "Grace Hopper",
    "Alan Turing",
    "Katherine Johnson",
    "Edsger Dijkstra",
    "Barbara Liskov",
    "Donald Knuth",
]

SKU_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # unambiguous, uppercase


def make_sku(case_index, item_index):
    """Deterministic 5-char SKU suffix from the case and item indices."""
    seed = case_index * 97 + item_index * 13 + 7
    chars = []
    for position in range(5):
        seed = (seed * 31 + position * 17 + 11) % (2 ** 31)
        chars.append(SKU_ALPHABET[seed % len(SKU_ALPHABET)])
    return "SKU-" + "".join(chars)


def build_order(case, schema):
    index = case["index"]
    name = CUSTOMER_NAMES[index % len(CUSTOMER_NAMES)]
    email_local = name.lower().replace(" ", ".")
    items = []
    for item_index in range(case["item_count"]):
        items.append(
            {
                "sku": make_sku(index, item_index),
                "quantity": 1 + (index + item_index * 3) % 9,
                "unit_price_cents": 199 + 150 * index + 425 * item_index,
            }
        )
    order = {
        "order_id": "ORD-%04d" % (1000 + index * 17),
        "customer": {"name": name, "email": "%s@example.com" % email_local},
        "status": case["status"],
        "currency": case["currency"],
        "items": items,
        "total_cents": sum(i["quantity"] * i["unit_price_cents"] for i in items),
    }

    # Sanity: enum values used by the manifest must exist in the schema proper.
    props = schema["properties"]
    assert order["status"] in props["status"]["enum"], order["status"]
    assert order["currency"] in props["currency"]["enum"], order["currency"]

    mutation = case.get("mutation")
    if mutation == "drop_customer_email":
        del order["customer"]["email"]
    elif mutation == "break_total":
        order["total_cents"] += 100
    elif mutation is not None:
        raise ValueError("unknown mutation: %r" % mutation)
    return order


def main(argv):
    out_dir = argv[1] if len(argv) > 1 else os.path.join(PROJECT_ROOT, "tests", "fixtures")
    with open(SCHEMA_PATH) as fh:
        schema = json.load(fh)

    os.makedirs(out_dir, exist_ok=True)
    cases = schema["x-fixtures"]["cases"]
    for case in cases:
        order = build_order(case, schema)
        path = os.path.join(out_dir, case["file"])
        with open(path, "w") as fh:
            json.dump(order, fh, indent=2, sort_keys=True)
            fh.write("\n")
    print("wrote %d fixtures to %s" % (len(cases), out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
