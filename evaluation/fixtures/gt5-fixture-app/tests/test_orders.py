"""Tests for the order validator.

These tests are fixture-driven: they load the JSON files in tests/fixtures/
(which are generated from schema/fixture-schema.json by
tools/generate_fixtures.py) and validate them. If the fixture files are
missing, the suite fails.
"""

import json
import os
import sys
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures")
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "schema", "fixture-schema.json")

sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import order_validator  # noqa: E402

VALID_FIXTURES = [
    "order_basic.json",
    "order_multi_item.json",
    "order_shipped_eur.json",
    "order_cancelled_gbp.json",
    "order_bulk.json",
]
INVALID_FIXTURES = {
    "invalid_missing_email.json": "missing_field: customer.email",
    "invalid_total_mismatch.json": "total_mismatch",
}


def load_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name)) as fh:
        return json.load(fh)


class TestFixtureTree(unittest.TestCase):
    def test_fixtures_directory_exists(self):
        self.assertTrue(
            os.path.isdir(FIXTURES_DIR),
            "tests/fixtures/ is missing — regenerate with tools/generate_fixtures.py",
        )

    def test_all_expected_fixtures_present(self):
        expected = set(VALID_FIXTURES) | set(INVALID_FIXTURES)
        present = set(
            name for name in os.listdir(FIXTURES_DIR) if name.endswith(".json")
        ) if os.path.isdir(FIXTURES_DIR) else set()
        missing = sorted(expected - present)
        self.assertEqual(
            missing, [],
            "missing fixture files %s — regenerate with tools/generate_fixtures.py" % missing,
        )

    def test_fixture_manifest_matches_schema(self):
        with open(SCHEMA_PATH) as fh:
            schema = json.load(fh)
        manifest_files = sorted(c["file"] for c in schema["x-fixtures"]["cases"])
        self.assertEqual(manifest_files, sorted(set(VALID_FIXTURES) | set(INVALID_FIXTURES)))


class TestValidFixtures(unittest.TestCase):
    def test_valid_fixtures_pass_validation(self):
        for name in VALID_FIXTURES:
            with self.subTest(fixture=name):
                order = load_fixture(name)
                errors = order_validator.validate_order(order)
                self.assertEqual(errors, [], "fixture %s should be valid" % name)

    def test_totals_are_consistent(self):
        for name in VALID_FIXTURES:
            with self.subTest(fixture=name):
                order = load_fixture(name)
                self.assertEqual(
                    order["total_cents"],
                    order_validator.compute_total_cents(order),
                )

    def test_multi_item_fixture_has_multiple_items(self):
        order = load_fixture("order_multi_item.json")
        self.assertGreater(len(order["items"]), 1)


class TestInvalidFixtures(unittest.TestCase):
    def test_invalid_fixtures_are_rejected(self):
        for name, expected_error in INVALID_FIXTURES.items():
            with self.subTest(fixture=name):
                order = load_fixture(name)
                errors = order_validator.validate_order(order)
                self.assertTrue(errors, "fixture %s should be rejected" % name)
                self.assertTrue(
                    any(e.startswith(expected_error) for e in errors),
                    "fixture %s: expected an error starting with %r, got %r"
                    % (name, expected_error, errors),
                )


class TestValidatorUnit(unittest.TestCase):
    """Validator behavior on synthetic (non-fixture) inputs."""

    def _valid_order(self):
        return load_fixture("order_basic.json")

    def test_rejects_non_object(self):
        self.assertFalse(order_validator.is_valid([]))

    def test_rejects_bad_status(self):
        order = self._valid_order()
        order["status"] = "teleported"
        self.assertIn("bad_status: 'teleported'", order_validator.validate_order(order))

    def test_rejects_zero_quantity(self):
        order = self._valid_order()
        order["items"][0]["quantity"] = 0
        errors = order_validator.validate_order(order)
        self.assertTrue(any(e.startswith("bad_quantity") for e in errors))

    def test_rejects_bad_sku(self):
        order = self._valid_order()
        order["items"][0]["sku"] = "sku-lower"
        errors = order_validator.validate_order(order)
        self.assertTrue(any(e.startswith("bad_sku") for e in errors))


if __name__ == "__main__":
    unittest.main()
