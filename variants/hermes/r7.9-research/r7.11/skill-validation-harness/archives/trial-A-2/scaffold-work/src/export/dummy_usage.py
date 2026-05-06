from src.export import serialize_csv, serialize_json, serialize_pdf, ExportFormat
from typing import List, Dict, Any

def test_dummy_usage():
    """
    Dummy usage to ensure serializers and ExportFormat are referenced.
    """
    data: List[Dict[str, Any]] = [
        {"id": 1, "name": "Test Item", "value": 100.0},
        {"id": 2, "name": "Another Item", "value": 200.0},
    ]

    # Test CSV
    csv_data = serialize_csv(data)
    assert isinstance(csv_data, str)
    assert "id,name,value" in csv_data

    # Test JSON
    json_data = serialize_json(data)
    assert isinstance(json_data, str)
    assert '"id": 1' in json_data

    # Test PDF
    pdf_data = serialize_pdf(data)
    assert isinstance(pdf_data, bytes)
    assert len(pdf_data) > 0

    # Test ExportFormat
    formats = [ExportFormat.CSV, ExportFormat.JSON, ExportFormat.PDF]
    assert len(formats) == 3
    assert ExportFormat.CSV.value == "csv"

if __name__ == "__main__":
    test_dummy_usage()
    print("Dummy usage test passed!")
