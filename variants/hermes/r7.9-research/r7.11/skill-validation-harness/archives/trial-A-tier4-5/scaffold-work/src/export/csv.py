import csv
import io
from typing import List, Dict

def serialize_csv(records: List[Dict]) -> str:
    if not records:
        return ""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()
