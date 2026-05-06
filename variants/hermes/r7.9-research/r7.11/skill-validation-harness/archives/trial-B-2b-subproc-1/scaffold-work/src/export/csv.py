import csv
import io

def serialize_csv(records: list[dict]) -> str:
    """
    Serializes a list of dictionaries into a CSV string.
    Handles empty list case by returning an empty string.
    """
    if not records:
        return ""

    output = io.StringIO()
    # Use the keys from the first record as headers
    fieldnames = list(records[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(records)
    
    return output.getvalue()
