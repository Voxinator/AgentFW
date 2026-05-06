"""Tests for src.export.csv (scaffold — worker will populate)."""
import os
import tempfile

from tests.fixtures import make_record


def test_basic_csv_has_header_and_row():
    """Worker should implement `export_to_csv(records, outpath)` such that
    given one record dict, output CSV has header row + 1 data row."""
    raise NotImplementedError("worker: implement export_to_csv and this test")


def test_empty_records_writes_header_only_or_empty():
    """Worker decides: empty list -> empty file, or header with 0 rows.
    Either is acceptable; test should assert on chosen behavior."""
    raise NotImplementedError("worker: implement export_to_csv and this test")
