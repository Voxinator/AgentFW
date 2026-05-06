import csv
import io
from typing import List, Dict, Any

def serialize_csv(records: List[Dict[str, Any]]) -> str:
    """
    Serializes a list of dictionaries to a CSV string.
    Uses the keys of the first dictionary as headers.
    """
    if not records:
        return ""

    output = io.StringIO()
    fieldnames = list(records[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(records)

    return output.getvalue()
