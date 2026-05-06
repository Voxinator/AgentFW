import pytest
from src.export.csv import serialize_csv
from src.export.json import serialize_json
from src.export.pdf import serialize_pdf
from src.export.formats import ExportFormat, Serializer

def test_phase1_wiring_csv():
    data = [{"id": 1, "name": "Alice"}]
    result = serialize_csv(data)
    assert "id,name" in result
    assert "1,Alice" in result

def test_phase1_wiring_json():
    data = [{"id": 1, "name": "Alice"}]
    result = serialize_json(data)
    assert '"id": 1' in result
    assert '"name": "Alice"' in result

def test_phase1_wiring_pdf():
    data = [{"id": 1, "name": "Alice"}]
    result = serialize_pdf(data)
    assert isinstance(result, bytes)
    assert len(result) > 0

def test_phase1_wiring_serializer_protocol():
    # Test the Serializer protocol usage via get_serializer
    from src.export.formats import get_serializer
    
    data = [{"id": 1, "name": "Alice"}]
    
    for fmt in ExportFormat:
        serializer = get_serializer(fmt)
        assert isinstance(serializer, Serializer)
        result = serializer.serialize(data)
        assert result is not None
