import csv
import json
import io
from typing import List, Dict, Union

# For PDF, we'll use reportlab which is standard for lightweight PDF generation in Python
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

def serialize_csv(records: List[Dict]) -> str:
    """Serializes a list of dicts to a CSV string."""
    if not records:
        return ""
    
    output = io.StringIO()
    # Use the keys from the first record as fieldnames
    fieldnames = list(records[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(records)
    
    return output.getvalue()

def serialize_json(records: List[Dict]) -> str:
    """Serializes a list of dicts to a JSON string."""
    return json.dumps(records, indent=2)

def serialize_pdf(records: List[Dict]) -> bytes:
    """Serializes a list of dicts to PDF bytes."""
    if not HAS_REPORTLAB:
        raise ImportError("reportlab is required for PDF serialization. Please install it.")
    
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    width, height = letter
    
    if not records:
        c.showPage()
        c.save()
        return output.getvalue()

    y_position = height - 50
    c.setFont("Helvetica", 10)
    
    for record in records:
        if y_position < 50:
            c.showPage()
            c.setFont("Helvetica", 10)
            y_position = height - 50
            
        line = str(record)
        # Simple truncation to avoid overflow
        if len(line) > 100:
            line = line[:97] + "..."
            
        c.drawString(50, y_position, line)
        y_position -= 15
        
    c.showPage()
    c.save()
    return output.getvalue()

def serialize(format_name: str, records: List[Dict]) -> Union[str, bytes]:
    """
    Internal dispatch for serializers.
    Returns str for CSV/JSON and bytes for PDF.
    """
    fmt = format_name.lower()
    if fmt == "csv":
        return serialize_csv(records)
    elif fmt == "json":
        return serialize_json(records)
    elif fmt == "pdf":
        return serialize_pdf(records)
    else:
        raise ValueError(f"Unsupported format: {format_name}")


if __name__ == "__main__":
    sample_data = [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 25, "city": "Los Angeles"},
        {"name": "Charlie", "age": 35, "city": "Chicago"},
    ]
    
    print("Testing JSON serialization:")
    print(serialize("json", sample_data))
    
    print("\nTesting CSV serialization:")
    print(serialize("csv", sample_data))

