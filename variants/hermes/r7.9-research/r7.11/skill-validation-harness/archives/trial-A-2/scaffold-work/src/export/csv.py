import csv
import io
from typing import List, Dict, Any

def serialize_csv(data: List[Dict[str, Any]]) -> str:
    """
    Serializes a list of dictionaries to a CSV string.
    Handles empty lists by returning an empty string.
    """
    if not data:
        return ""

    output = io.StringIO()
    fieldnames = list(data[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()
