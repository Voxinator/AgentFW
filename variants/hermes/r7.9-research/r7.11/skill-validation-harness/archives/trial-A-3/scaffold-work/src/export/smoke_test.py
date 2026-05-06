from .formats import ExportFormat
from .csv import serialize_csv
from .json import serialize_json
from .pdf import serialize_pdf

def run_smoke_test():
    """
    A simple smoke test to ensure serializers are working.
    This provides a call site for static analysis.
    """
    sample_data = {"id": 1, "name": "test_item", "value": 100.0}
    
    # Test JSON
    json_out = serialize_json(sample_data)
    assert isinstance(json_out, str)
    
    # Test CSV
    csv_out = serialize_csv([sample_data])
    assert isinstance(csv_out, str)
    
    # Test PDF
    pdf_out = serialize_pdf(sample_data)
    assert isinstance(pdf_out, bytes)
    
    print("Smoke test passed successfully!")

if __name__ == "__main__":
    run_smoke_test()
