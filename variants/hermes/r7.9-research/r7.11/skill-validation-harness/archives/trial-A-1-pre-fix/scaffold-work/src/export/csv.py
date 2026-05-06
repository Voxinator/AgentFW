import csv
import io

def serialize_csv(data: list[dict]) -> str:
    """
    Serializes a list of dictionaries into a CSV string.
    
    Args:
        data: A list of dictionaries representing the rows.
        
    Returns:
        A CSV formatted string.
    """
    if not data:
        return ""
    
    output = io.StringIO()
    fieldnames = data[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()
