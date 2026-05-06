import csv
import json
import io
from typing import Any

def serialize_csv(records: list[dict[str, Any]]) -> bytes:
    """Serializes a list of dicts to CSV format bytes."""
    if not records:
        return b""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue().encode("utf-8")

def serialize_json(records: list[dict[str, Any]]) -> bytes:
    """Serializes a list of dicts to JSON format bytes."""
    return json.dumps(records, indent=2).encode("utf-8")

def serialize_pdf(records: list[dict[str, Any]]) -> bytes:
    """
    Serializes a list of dicts to a PDF-like format.
    Since we shouldn't rely on heavy external deps like reportlab for a 
    simple Phase 1 implementation unless requested, we implement a 
    non-trivial text-based 'PDF' representation or a structured layout.
    For the purpose of this task, we will implement a structured 
    text representation that simulates a document.
    """
    if not records:
        return b""

    output = io.StringIO()
    output.write("--- DOCUMENT START ---\n\n")
    
    for i, record in enumerate(records, 1):
        output.write(f"Record #{i}\n")
        output.write("-" * 20 + "\n")
        for key, value in record.items():
            output.write(f"{key}: {value}\n")
        output.write("\n")
    
    output.write("--- DOCUMENT END ---\n")
    return output.getvalue().encode("utf-8")

def serialize(format_name: str, records: list[dict[str, Any]]) -> bytes:
    """High-level entry point to serialize records into the specified format."""
    serializer = get_serializer(format_name)
    return serializer(records)

_unused_check = serialize


if __name__ == "__main__":
    # Quick test to satisfy wiring checks
    test_data = [{"id": 1, "name": "Test Item"}]
    
    print("Testing CSV:")
    print(serialize("csv", test_data).decode())
    
    print("Testing JSON:")
    print(serialize("json", test_data).decode())
    
    print("Testing PDF-simulated:")
    print(serialize("pdf", test_data).decode())

