"""Tests for src.export.csv (scaffold — worker will populate)."""
import os
import tempfile
import csv
import io

from tests.fixtures import make_record
from src.export.csv import serialize_csv


def test_basic_csv_has_header_and_row():
    """Worker should implement `export_to_csv(records, outpath)` such that
    given one record dict, output CSV has header row + 1 data row."""
    records = [make_record()]
    csv_content = serialize_csv(records)
    
    # Parse the result to verify
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]["owner_id"] == "u1"
    assert int(rows[0]["value"]) == 42
    assert rows[0]["name"] == "record-42"


def test_empty_records_writes_header_only_or_empty():
    """Worker decides: empty list -> empty file, or header with 0 rows.
    Either is acceptable; test should assert on chosen behavior."""
    records = []
    csv_content = serialize_csv(records)
    
    # Based on implementation: returns "" for empty list
    assert csv_content == ""
