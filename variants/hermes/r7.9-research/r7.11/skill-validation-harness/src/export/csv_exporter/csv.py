import csv
import io
from typing import List, Dict

def serialize_csv(records: List[Dict]) -> str:
    """
    Serializes a list of dictionaries into a CSV string.
    """
    if not records:
        return ""
    
    output = io.StringIO()
    # Use keys from the first record as fieldnames
    fieldnames = records[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(records)
    
    return output.getvalue()
