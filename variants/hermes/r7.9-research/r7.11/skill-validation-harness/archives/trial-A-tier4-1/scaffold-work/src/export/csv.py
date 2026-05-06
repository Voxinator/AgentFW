import csv
import io

def serialize_csv(records: list[dict]) -> str:
    if not records:
        return ""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()
