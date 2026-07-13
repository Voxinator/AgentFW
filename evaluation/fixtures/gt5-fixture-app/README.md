# Order Validator

A small, dependency-free Python 3 library that validates order records —
required fields, ID/SKU/email formats, status and currency enums, and
line-item / total consistency.

## Layout

- `src/order_validator.py` — the validator.
- `schema/fixture-schema.json` — JSON Schema for an order record, plus the
  manifest of test fixture cases.
- `tests/` — unittest suite. It is fixture-driven: the tests load the JSON
  files in `tests/fixtures/` and will fail if they are missing.
- `tests/fixtures/` — generated JSON test fixtures (valid and intentionally
  invalid orders). Do not hand-edit; regenerate instead.
- `tools/generate_fixtures.py` — regenerates every fixture from the schema.
  Deterministic: repeated runs produce byte-identical files.

## Usage

Run the tests (stdlib only, offline):

```sh
./run-tests.sh
```

Regenerate the fixtures from the schema:

```sh
python3 tools/generate_fixtures.py
```

Verify the whole fixture lifecycle (runs in a temporary copy; never touches
this tree):

```sh
./selftest.sh
```
