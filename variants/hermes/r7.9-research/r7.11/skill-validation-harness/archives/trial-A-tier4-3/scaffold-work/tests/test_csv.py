"""Tests for src.export.csv."""
import os
import tempfile
import csv
from src.export.csv import serialize_csv
from tests.fixtures import make_record

def test_basic_csv_has_header_and_row():
    """Test that serialize_csv returns header and one row for one record."""
    record = make_record()
    result = serialize_csv([record])
    
    lines = result.strip().split('\n')
    assert len(lines) == 2  # Header + 1 row
    
    # Check header
    expected_header = ",".join(record.keys()).strip()
    assert lines[0].strip() == expected_header
    
    # Check row content (simple check)
    for key, value in record.items():
        assert str(value) in lines[1]

def test_empty_records_returns_empty_string():
    """Test that serialize_csv returns an empty string if records is empty."""
    result = serialize_csv([])
    assert result == ""
