import pytest
from src.export.serializers import serialize_csv, serialize_json, serialize_pdf, serialize

def test_serialize_csv_basic():
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    result = serialize_csv(data)
    assert "id,name" in result
    assert "1,Alice" in result
    assert "2,Bob" in result

def test_serialize_csv_empty():
    assert serialize_csv([]) == ""

def test_serialize_json_basic():
    data = [{"id": 1, "name": "Alice"}]
    result = serialize_json(data)
    assert '"id": 1' in result
    assert '"name": "Alice"' in result

def test_serialize_json_empty():
    assert serialize_json([]) == "[]"

def test_serialize_pdf_basic():
    data = [{"id": 1, "name": "Alice"}]
    result = serialize_pdf(data)
    assert isinstance(result, bytes)
    assert len(result) > 0

def test_serialize_pdf_empty():
    assert serialize_pdf([]) == b""

def test_serialize_dispatch():
    data = [{"id": 1, "name": "Alice"}]
    assert isinstance(serialize(data, "csv"), str)
    assert isinstance(serialize(data, "json"), str)
    assert isinstance(serialize(data, "pdf"), bytes)

def test_serialize_invalid_format():
    with pytest.raises(ValueError, match="Unsupported format: xml"):
        serialize([], "xml")
